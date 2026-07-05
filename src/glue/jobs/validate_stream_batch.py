"""Validate one streaming batch before KPI transformation.

This AWS Glue PySpark job writes a validation report to S3 and raises an
exception when any mandatory integrity check fails. Step Functions catches that
exception and routes the source object to the DLQ/quarantine path.
"""

from __future__ import annotations

import json
import re
import sys
from collections.abc import Iterable
from functools import reduce
from operator import or_

import boto3
from awsglue.utils import getResolvedOptions
from music_etl.constants import REQUIRED_COLUMNS
from music_etl.reports import CheckResult, build_validation_report, count_check, pass_check
from music_etl.s3_paths import build_execution_id, normalise_event_key, s3_uri
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

ARGS = [
    "bucket",
    "stream_key",
    "songs_key",
    "users_key",
    "report_prefix",
    "late_arrival_days",
    "execution_id",
]


def read_csv(spark: SparkSession, uri: str) -> DataFrame:
    return (
        spark.read.option("header", "true")
        .option("mode", "PERMISSIVE")
        .option("quote", '"')
        .option("escape", '"')
        .csv(uri)
    )


def has_columns(df: DataFrame, columns: Iterable[str]) -> bool:
    return set(columns).issubset(set(df.columns))


def blank_condition(columns: Iterable[str]):
    return reduce(
        or_,
        [(F.col(column).isNull()) | (F.trim(F.col(column)) == "") for column in columns],
    )


def count_blank_required(df: DataFrame, columns: Iterable[str]) -> int:
    present_columns = [column for column in columns if column in df.columns]
    if not present_columns:
        return 0
    return df.where(blank_condition(present_columns)).count()


def missing_column_checks(dataset: str, df: DataFrame) -> list[CheckResult]:
    missing = sorted(REQUIRED_COLUMNS[dataset] - set(df.columns))
    return [
        count_check(
            pillar="completeness",
            name=f"{dataset}_required_columns",
            observed=len(missing),
            threshold=0,
            details={"missing_columns": missing},
        )
    ]


def completeness_checks(dataset: str, df: DataFrame) -> list[CheckResult]:
    return [
        *missing_column_checks(dataset, df),
        count_check(
            pillar="completeness",
            name=f"{dataset}_required_values",
            observed=count_blank_required(df, REQUIRED_COLUMNS[dataset]),
            threshold=0,
        ),
    ]


def duplicate_count(df: DataFrame, columns: list[str]) -> int:
    if not has_columns(df, columns):
        return 0
    return df.groupBy(*columns).count().where(F.col("count") > 1).count()


def uniqueness_checks(songs: DataFrame, users: DataFrame, streams: DataFrame) -> list[CheckResult]:
    return [
        count_check(
            pillar="uniqueness",
            name="songs_unique_track_id",
            observed=duplicate_count(songs, ["track_id"]),
            threshold=0,
        ),
        count_check(
            pillar="uniqueness",
            name="users_unique_user_id",
            observed=duplicate_count(users, ["user_id"]),
            threshold=0,
        ),
        count_check(
            pillar="uniqueness",
            name="streams_unique_event_identity",
            observed=duplicate_count(streams, ["user_id", "track_id", "listen_time"]),
            threshold=0,
        ),
    ]


def with_normalised_columns(songs: DataFrame, users: DataFrame, streams: DataFrame):
    song_dim = songs
    if "track_id" in songs.columns:
        song_dim = song_dim.withColumn("track_id_norm", F.trim(F.col("track_id")))
    if "duration_ms" in songs.columns:
        song_dim = song_dim.withColumn("duration_ms_long", F.col("duration_ms").cast("long"))

    user_dim = users
    if "user_id" in users.columns:
        user_dim = user_dim.withColumn("user_id_norm", F.trim(F.col("user_id")))
    if "created_at" in users.columns:
        user_dim = user_dim.withColumn("created_date", F.to_date(F.col("created_at")))
    if "user_age" in users.columns:
        user_dim = user_dim.withColumn("user_age_int", F.col("user_age").cast("int"))

    stream_events = streams
    if "track_id" in streams.columns:
        stream_events = stream_events.withColumn("track_id_norm", F.trim(F.col("track_id")))
    if "user_id" in streams.columns:
        stream_events = stream_events.withColumn("user_id_norm", F.trim(F.col("user_id")))
    if "listen_time" in streams.columns:
        stream_events = stream_events.withColumn(
            "listen_ts",
            F.coalesce(
                F.to_timestamp(F.col("listen_time"), "yyyy-MM-dd HH:mm:ss"),
                F.to_timestamp(F.col("listen_time")),
            ),
        ).withColumn("metric_date", F.to_date(F.col("listen_ts")))

    return song_dim, user_dim, stream_events


def validity_checks(songs: DataFrame, users: DataFrame, streams: DataFrame) -> list[CheckResult]:
    checks: list[CheckResult] = []

    if "duration_ms_long" in songs.columns:
        checks.append(
            count_check(
                pillar="validity",
                name="songs_positive_duration_ms",
                observed=songs.where(
                    (F.col("duration_ms_long").isNull()) | (F.col("duration_ms_long") <= 0)
                ).count(),
                threshold=0,
            )
        )

    if "user_age_int" in users.columns:
        checks.append(
            count_check(
                pillar="validity",
                name="users_age_range",
                observed=users.where(
                    (F.col("user_age_int").isNull())
                    | (F.col("user_age_int") < 0)
                    | (F.col("user_age_int") > 120)
                ).count(),
                threshold=0,
            )
        )

    if "created_date" in users.columns:
        checks.append(
            count_check(
                pillar="validity",
                name="users_created_at_parseable",
                observed=users.where(F.col("created_date").isNull()).count(),
                threshold=0,
            )
        )

    if "listen_ts" in streams.columns:
        checks.append(
            count_check(
                pillar="validity",
                name="streams_listen_time_parseable",
                observed=streams.where(F.col("listen_ts").isNull()).count(),
                threshold=0,
            )
        )

    return checks


def consistency_checks(songs: DataFrame, users: DataFrame, streams: DataFrame) -> list[CheckResult]:
    checks: list[CheckResult] = []

    if has_columns(songs, ["track_id_norm"]) and has_columns(streams, ["track_id_norm"]):
        missing_songs = (
            streams.select("track_id_norm")
            .distinct()
            .join(songs.select("track_id_norm").distinct(), "track_id_norm", "left_anti")
            .count()
        )
        checks.append(
            count_check(
                pillar="consistency",
                name="streams_track_id_exists_in_songs",
                observed=missing_songs,
                threshold=0,
            )
        )

    if has_columns(users, ["user_id_norm"]) and has_columns(streams, ["user_id_norm"]):
        missing_users = (
            streams.select("user_id_norm")
            .distinct()
            .join(users.select("user_id_norm").distinct(), "user_id_norm", "left_anti")
            .count()
        )
        checks.append(
            count_check(
                pillar="consistency",
                name="streams_user_id_exists_in_users",
                observed=missing_users,
                threshold=0,
            )
        )

    return checks


def stream_date_from_key(stream_key: str) -> str | None:
    match = re.search(r"raw/streams/(\d{4})/(\d{2})/(\d{2})/", stream_key)
    if not match:
        return None
    return "-".join(match.groups())


def timeliness_checks(
    stream_key: str, streams: DataFrame, late_arrival_days: int
) -> list[CheckResult]:
    checks: list[CheckResult] = []
    if "listen_ts" not in streams.columns:
        return checks

    checks.append(
        count_check(
            pillar="timeliness",
            name="streams_not_future_dated",
            observed=streams.where(F.col("listen_ts") > F.current_timestamp()).count(),
            threshold=0,
        )
    )

    checks.append(
        count_check(
            pillar="timeliness",
            name="streams_within_late_arrival_window",
            observed=streams.where(
                F.col("listen_ts")
                < F.expr(f"current_timestamp() - INTERVAL {int(late_arrival_days)} DAYS")
            ).count(),
            threshold=0,
            details={"late_arrival_days": late_arrival_days},
        )
    )

    expected_date = stream_date_from_key(stream_key)
    if expected_date:
        checks.append(
            count_check(
                pillar="timeliness",
                name="streams_metric_date_matches_s3_partition",
                observed=streams.where(F.col("metric_date") != F.lit(expected_date)).count(),
                threshold=0,
                details={"expected_metric_date": expected_date},
            )
        )
    else:
        checks.append(
            pass_check(
                pillar="timeliness",
                name="streams_s3_partition_date_not_provided",
                observed="not_applicable",
                threshold="not_applicable",
            )
        )

    return checks


def accuracy_checks(songs: DataFrame, users: DataFrame, streams: DataFrame) -> list[CheckResult]:
    required = [
        has_columns(songs, ["track_id_norm", "duration_ms_long"]),
        has_columns(users, ["user_id_norm"]),
        has_columns(streams, ["track_id_norm", "user_id_norm"]),
    ]
    if not all(required):
        return [
            count_check(
                pillar="accuracy",
                name="accepted_stream_reconciliation",
                observed=1,
                threshold=0,
                details={"reason": "missing columns prevented reconciliation"},
            )
        ]

    accepted = (
        streams.join(songs.select("track_id_norm", "duration_ms_long"), "track_id_norm", "inner")
        .join(users.select("user_id_norm"), "user_id_norm", "inner")
        .where(F.col("duration_ms_long") > 0)
    )
    stream_count = streams.count()
    accepted_count = accepted.count()
    delta = abs(stream_count - accepted_count)
    return [
        count_check(
            pillar="accuracy",
            name="accepted_stream_reconciliation",
            observed=delta,
            threshold=0,
            details={"expected": stream_count, "accepted": accepted_count},
        )
    ]


def write_report(bucket: str, report_prefix: str, execution_id: str, report: dict) -> str:
    report_key = f"{report_prefix.strip('/')}/{execution_id}/validation_report.json"
    boto3.client("s3").put_object(
        Bucket=bucket,
        Key=report_key,
        Body=json.dumps(report, indent=2, sort_keys=True).encode("utf-8"),
        ContentType="application/json",
    )
    return report_key


def main() -> None:
    args = getResolvedOptions(sys.argv, ARGS + ["JOB_NAME"])
    bucket = args["bucket"]
    stream_key = normalise_event_key(args["stream_key"])
    execution_id = args.get("execution_id") or build_execution_id("validation")
    late_arrival_days = int(args["late_arrival_days"])

    spark = SparkSession.builder.appName(args["JOB_NAME"]).getOrCreate()

    songs = read_csv(spark, s3_uri(bucket, args["songs_key"])).cache()
    users = read_csv(spark, s3_uri(bucket, args["users_key"])).cache()
    streams = read_csv(spark, s3_uri(bucket, stream_key)).cache()

    row_counts = {
        "songs": songs.count(),
        "users": users.count(),
        "streams": streams.count(),
    }

    song_dim, user_dim, stream_events = with_normalised_columns(songs, users, streams)
    song_dim.cache()
    user_dim.cache()
    stream_events.cache()

    checks: list[CheckResult] = []
    checks.extend(completeness_checks("songs", songs))
    checks.extend(completeness_checks("users", users))
    checks.extend(completeness_checks("streams", streams))
    checks.extend(uniqueness_checks(songs, users, streams))
    checks.extend(validity_checks(song_dim, user_dim, stream_events))
    checks.extend(consistency_checks(song_dim, user_dim, stream_events))
    checks.extend(timeliness_checks(stream_key, stream_events, late_arrival_days))
    checks.extend(accuracy_checks(song_dim, user_dim, stream_events))

    report = build_validation_report(
        execution_id=execution_id,
        bucket=bucket,
        stream_key=stream_key,
        row_counts=row_counts,
        checks=checks,
    )
    report_key = write_report(bucket, args["report_prefix"], execution_id, report)

    failed = [check for check in checks if check.status == "FAIL"]
    if failed:
        failed_names = ", ".join(check.name for check in failed)
        raise RuntimeError(
            f"Validation failed; report=s3://{bucket}/{report_key}; checks={failed_names}"
        )

    print(f"Validation passed; report=s3://{bucket}/{report_key}")


if __name__ == "__main__":
    main()
