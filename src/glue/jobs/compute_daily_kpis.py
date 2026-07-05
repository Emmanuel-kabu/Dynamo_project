"""Compute daily music streaming KPI data products with AWS Glue PySpark."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone

import boto3
from awsglue.utils import getResolvedOptions
from music_etl import DATA_PRODUCT_VERSION
from music_etl.s3_paths import normalise_event_key, parent_prefix, s3_uri
from pyspark.sql import DataFrame, SparkSession, Window
from pyspark.sql import functions as F

ARGS = [
    "bucket",
    "stream_key",
    "songs_key",
    "output_prefix",
    "execution_id",
]


def read_csv(spark: SparkSession, paths: list[str] | str) -> DataFrame:
    return (
        spark.read.option("header", "true")
        .option("mode", "PERMISSIVE")
        .option("quote", '"')
        .option("escape", '"')
        .csv(paths)
    )


def list_csv_keys(bucket: str, prefix: str) -> list[str]:
    client = boto3.client("s3")
    keys: list[str] = []
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix.strip("/") + "/"):
        for item in page.get("Contents", []):
            key = item["Key"]
            if key.lower().endswith(".csv"):
                keys.append(key)
    return sorted(keys)


def daily_stream_keys(bucket: str, stream_key: str) -> list[str]:
    raw_day_prefix = parent_prefix(stream_key)
    archive_day_prefix = f"archive/{raw_day_prefix}"
    keys = {*list_csv_keys(bucket, raw_day_prefix), *list_csv_keys(bucket, archive_day_prefix)}
    if stream_key not in keys:
        keys.add(stream_key)
    return sorted(keys)


def metric_date_from_key(stream_key: str) -> str | None:
    match = re.search(r"raw/streams/(\d{4})/(\d{2})/(\d{2})/", stream_key)
    if not match:
        return None
    return "-".join(match.groups())


def enrich_streams(streams: DataFrame, songs: DataFrame) -> DataFrame:
    stream_events = (
        streams.withColumn("user_id", F.trim(F.col("user_id")))
        .withColumn("track_id", F.trim(F.col("track_id")))
        .withColumn(
            "listen_ts",
            F.coalesce(
                F.to_timestamp(F.col("listen_time"), "yyyy-MM-dd HH:mm:ss"),
                F.to_timestamp(F.col("listen_time")),
            ),
        )
        .withColumn("metric_date", F.to_date(F.col("listen_ts")).cast("string"))
        .dropDuplicates(["user_id", "track_id", "listen_time"])
    )

    song_dim = (
        songs.withColumn("track_id", F.trim(F.col("track_id")))
        .withColumn("duration_ms", F.col("duration_ms").cast("long"))
        .select("track_id", "track_genre", "track_name", "artists", "duration_ms")
    )

    return stream_events.join(song_dim, "track_id", "inner").where(F.col("duration_ms") > 0)


def with_metadata(df: DataFrame, execution_id: str, generated_at: str) -> DataFrame:
    return (
        df.withColumn("generated_at", F.lit(generated_at))
        .withColumn("source_execution_id", F.lit(execution_id))
        .withColumn("version", F.lit(DATA_PRODUCT_VERSION))
        .withColumn("dt", F.col("metric_date"))
    )


def compute_daily_genre_kpis(
    enriched: DataFrame, execution_id: str, generated_at: str
) -> DataFrame:
    metrics = (
        enriched.groupBy(F.col("metric_date"), F.col("track_genre").alias("genre"))
        .agg(
            F.count(F.lit(1)).cast("long").alias("listen_count"),
            F.countDistinct("user_id").cast("long").alias("unique_listeners"),
            F.sum("duration_ms").cast("long").alias("total_listening_time_ms"),
        )
        .withColumn(
            "avg_listening_time_ms_per_user",
            F.round(F.col("total_listening_time_ms") / F.col("unique_listeners"), 6),
        )
    )
    return with_metadata(metrics, execution_id, generated_at)


def compute_top_songs(enriched: DataFrame, execution_id: str, generated_at: str) -> DataFrame:
    song_counts = (
        enriched.groupBy(
            "metric_date",
            F.col("track_genre").alias("genre"),
            "track_id",
            "track_name",
            "artists",
        )
        .agg(F.count(F.lit(1)).cast("long").alias("listen_count"))
    )
    window = Window.partitionBy("metric_date", "genre").orderBy(
        F.desc("listen_count"), F.asc("track_name"), F.asc("track_id")
    )
    ranked = (
        song_counts.withColumn("rank", F.row_number().over(window))
        .where(F.col("rank") <= 3)
        .withColumn("metric_date_genre", F.concat_ws("#", F.col("metric_date"), F.col("genre")))
    )
    return with_metadata(ranked, execution_id, generated_at)


def compute_top_genres(
    daily_genre_kpis: DataFrame, execution_id: str, generated_at: str
) -> DataFrame:
    window = Window.partitionBy("metric_date").orderBy(F.desc("listen_count"), F.asc("genre"))
    ranked = (
        daily_genre_kpis.select("metric_date", "genre", "listen_count", "unique_listeners")
        .withColumn("rank", F.row_number().over(window))
        .where(F.col("rank") <= 5)
    )
    return with_metadata(ranked, execution_id, generated_at)


def write_product(df: DataFrame, bucket: str, output_prefix: str, product_name: str) -> str:
    output_uri = s3_uri(bucket, f"{output_prefix.strip('/')}/{product_name}")
    (
        df.write.mode("overwrite")
        .partitionBy("dt")
        .option("compression", "gzip")
        .json(output_uri)
    )
    return output_uri


def write_summary(bucket: str, output_prefix: str, execution_id: str, summary: dict) -> str:
    key = f"{output_prefix.strip('/')}/audit/{execution_id}/kpi_summary.json"
    boto3.client("s3").put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(summary, indent=2, sort_keys=True).encode("utf-8"),
        ContentType="application/json",
    )
    return key


def main() -> None:
    args = getResolvedOptions(sys.argv, ARGS + ["JOB_NAME"])
    bucket = args["bucket"]
    stream_key = normalise_event_key(args["stream_key"])
    execution_id = args["execution_id"]
    output_prefix = args["output_prefix"].strip("/")
    generated_at = datetime.now(timezone.utc).isoformat()

    spark = SparkSession.builder.appName(args["JOB_NAME"]).getOrCreate()
    spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")

    stream_keys = daily_stream_keys(bucket, stream_key)
    stream_paths = [s3_uri(bucket, key) for key in stream_keys]
    songs_path = s3_uri(bucket, args["songs_key"])

    streams = read_csv(spark, stream_paths)
    songs = read_csv(spark, songs_path)
    enriched = enrich_streams(streams, songs).cache()

    expected_date = metric_date_from_key(stream_key)
    if expected_date:
        enriched = enriched.where(F.col("metric_date") == expected_date).cache()

    accepted_stream_count = enriched.count()
    if accepted_stream_count == 0:
        raise RuntimeError(f"No accepted stream rows found for {stream_key}")

    daily_genre_kpis = compute_daily_genre_kpis(enriched, execution_id, generated_at).cache()
    daily_genre_top_songs = compute_top_songs(enriched, execution_id, generated_at).cache()
    daily_top_genres = compute_top_genres(daily_genre_kpis, execution_id, generated_at).cache()

    reconciled_count = daily_genre_kpis.agg(F.sum("listen_count").alias("count")).first()["count"]
    if accepted_stream_count != reconciled_count:
        raise RuntimeError(
            "KPI reconciliation failed: "
            f"accepted_stream_count={accepted_stream_count}, genre_listen_count={reconciled_count}"
        )

    product_paths = {
        "daily_genre_kpis": write_product(
            daily_genre_kpis, bucket, output_prefix, "daily_genre_kpis"
        ),
        "daily_genre_top_songs": write_product(
            daily_genre_top_songs, bucket, output_prefix, "daily_genre_top_songs"
        ),
        "daily_top_genres": write_product(
            daily_top_genres, bucket, output_prefix, "daily_top_genres"
        ),
    }

    summary_key = write_summary(
        bucket,
        output_prefix,
        execution_id,
        {
            "execution_id": execution_id,
            "generated_at": generated_at,
            "stream_key": stream_key,
            "included_stream_keys": stream_keys,
            "accepted_stream_count": accepted_stream_count,
            "daily_genre_kpi_count": daily_genre_kpis.count(),
            "daily_genre_top_song_count": daily_genre_top_songs.count(),
            "daily_top_genre_count": daily_top_genres.count(),
            "product_paths": product_paths,
        },
    )

    print(f"KPI products written: {json.dumps(product_paths, sort_keys=True)}")
    print(f"KPI summary written: s3://{bucket}/{summary_key}")


if __name__ == "__main__":
    main()
