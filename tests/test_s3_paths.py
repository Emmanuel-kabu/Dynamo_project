import pytest
from music_etl.s3_paths import normalise_event_key, parent_prefix, parse_s3_uri, s3_uri


def test_parse_s3_uri_round_trips_bucket_and_key():
    parsed = parse_s3_uri("s3://example-bucket/raw/streams/file.csv")

    assert parsed.bucket == "example-bucket"
    assert parsed.key == "raw/streams/file.csv"
    assert parsed.uri == "s3://example-bucket/raw/streams/file.csv"


def test_parse_s3_uri_rejects_invalid_values():
    with pytest.raises(ValueError, match="Expected s3:// URI"):
        parse_s3_uri("https://example-bucket/raw/file.csv")


def test_s3_uri_normalises_leading_slash():
    assert s3_uri("bucket", "/raw/file.csv") == "s3://bucket/raw/file.csv"


def test_normalise_event_key_decodes_eventbridge_encoding():
    assert normalise_event_key("raw/streams/2024/06/25/my+file.csv") == (
        "raw/streams/2024/06/25/my file.csv"
    )


def test_parent_prefix_returns_directory_part():
    assert parent_prefix("raw/streams/2024/06/25/streams1.csv") == "raw/streams/2024/06/25"
