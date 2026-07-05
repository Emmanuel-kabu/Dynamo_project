"""S3 path utilities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import unquote_plus


@dataclass(frozen=True)
class S3Uri:
    bucket: str
    key: str

    @property
    def uri(self) -> str:
        return f"s3://{self.bucket}/{self.key}"


def parse_s3_uri(value: str) -> S3Uri:
    if not value.startswith("s3://"):
        raise ValueError(f"Expected s3:// URI, got: {value}")
    without_scheme = value.removeprefix("s3://")
    bucket, separator, key = without_scheme.partition("/")
    if not bucket or not separator or not key:
        raise ValueError(f"Invalid S3 URI: {value}")
    return S3Uri(bucket=bucket, key=key)


def s3_uri(bucket: str, key: str) -> str:
    return S3Uri(bucket=bucket, key=key.lstrip("/")).uri


def normalise_event_key(key: str) -> str:
    return unquote_plus(key).lstrip("/")


def build_execution_id(prefix: str = "exec") -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{prefix}-{timestamp}"


def parent_prefix(key: str) -> str:
    normalised = key.strip("/")
    parent, _, _ = normalised.rpartition("/")
    return parent
