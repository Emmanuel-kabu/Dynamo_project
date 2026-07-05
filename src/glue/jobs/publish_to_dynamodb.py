"""Publish curated KPI data products to DynamoDB.

This Glue Python Shell job is idempotent: each product uses deterministic keys
and batch_writer overwrites records for the same metric date, genre, rank, and
track identity.
"""

from __future__ import annotations

import gzip
import io
import json
import re
import sys
from collections.abc import Iterable
from datetime import datetime, timezone

import boto3
from awsglue.utils import getResolvedOptions
from music_etl.dynamodb import remove_nulls, to_dynamodb_value
from music_etl.s3_paths import normalise_event_key

ARGS = [
    "bucket",
    "stream_key",
    "output_prefix",
    "execution_id",
    "daily_genre_kpis_table",
    "daily_genre_top_songs_table",
    "daily_top_genres_table",
    "pipeline_audit_table",
]


PRODUCT_CONFIG = {
    "daily_genre_kpis": {
        "table_arg": "daily_genre_kpis_table",
        "pkeys": ["metric_date", "genre"],
    },
    "daily_genre_top_songs": {
        "table_arg": "daily_genre_top_songs_table",
        "pkeys": ["metric_date_genre", "rank"],
    },
    "daily_top_genres": {
        "table_arg": "daily_top_genres_table",
        "pkeys": ["metric_date", "rank"],
    },
}


def metric_date_from_key(stream_key: str) -> str:
    match = re.search(r"raw/streams/(\d{4})/(\d{2})/(\d{2})/", stream_key)
    if not match:
        raise ValueError(f"Could not derive metric date from stream key: {stream_key}")
    return "-".join(match.groups())


def list_objects(bucket: str, prefix: str) -> list[str]:
    client = boto3.client("s3")
    keys: list[str] = []
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix.strip("/") + "/"):
        for item in page.get("Contents", []):
            key = item["Key"]
            if not key.endswith("/") and not key.endswith("_SUCCESS"):
                keys.append(key)
    return sorted(keys)


def iter_json_lines(bucket: str, keys: Iterable[str]):
    client = boto3.client("s3")
    for key in keys:
        response = client.get_object(Bucket=bucket, Key=key)
        payload = response["Body"].read()
        if key.endswith(".gz"):
            with gzip.GzipFile(fileobj=io.BytesIO(payload)) as gz_file:
                text = gz_file.read().decode("utf-8")
        else:
            text = payload.decode("utf-8")

        for line in text.splitlines():
            if line.strip():
                yield json.loads(line)


def publish_records(table, pkeys: list[str], records: list[dict]) -> int:
    with table.batch_writer(overwrite_by_pkeys=pkeys) as batch:
        for record in records:
            item = to_dynamodb_value(remove_nulls(record))
            batch.put_item(Item=item)
    return len(records)


def audit_success(table, execution_id: str, stream_key: str, counts: dict[str, int]) -> None:
    now = datetime.now(timezone.utc).isoformat()
    table.put_item(
        Item=to_dynamodb_value(
            {
                "execution_id": execution_id,
                "event_ts": now,
                "status": "PUBLISHED",
                "stream_key": stream_key,
                "published_counts": counts,
            }
        )
    )


def main() -> None:
    args = getResolvedOptions(sys.argv, ARGS + ["JOB_NAME"])
    bucket = args["bucket"]
    stream_key = normalise_event_key(args["stream_key"])
    output_prefix = args["output_prefix"].strip("/")
    execution_id = args["execution_id"]
    metric_date = metric_date_from_key(stream_key)

    dynamodb = boto3.resource("dynamodb")
    published_counts: dict[str, int] = {}

    for product_name, config in PRODUCT_CONFIG.items():
        product_prefix = f"{output_prefix}/{product_name}/dt={metric_date}"
        keys = list_objects(bucket, product_prefix)
        if not keys:
            raise RuntimeError(f"No curated files found for {product_name}: s3://{bucket}/{product_prefix}")

        records = list(iter_json_lines(bucket, keys))
        if not records:
            raise RuntimeError(f"No curated records found for {product_name}: s3://{bucket}/{product_prefix}")

        table = dynamodb.Table(args[config["table_arg"]])
        published_counts[product_name] = publish_records(table, config["pkeys"], records)

    audit_table = dynamodb.Table(args["pipeline_audit_table"])
    audit_success(audit_table, execution_id, stream_key, published_counts)

    print(f"Published DynamoDB data products: {json.dumps(published_counts, sort_keys=True)}")


if __name__ == "__main__":
    main()
