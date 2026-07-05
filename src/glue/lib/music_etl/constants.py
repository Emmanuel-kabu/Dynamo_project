"""Project constants shared by Glue jobs and tests."""

DATA_PRODUCT_VERSION = 1

REQUIRED_COLUMNS = {
    "songs": {
        "track_id",
        "artists",
        "album_name",
        "track_name",
        "duration_ms",
        "track_genre",
    },
    "users": {
        "user_id",
        "user_country",
        "created_at",
    },
    "streams": {
        "user_id",
        "track_id",
        "listen_time",
    },
}

QUALITY_PILLARS = (
    "completeness",
    "uniqueness",
    "validity",
    "consistency",
    "timeliness",
    "accuracy",
)

DYNAMODB_PRODUCTS = {
    "daily_genre_kpis": {
        "hash_key": "metric_date",
        "range_key": "genre",
    },
    "daily_genre_top_songs": {
        "hash_key": "metric_date_genre",
        "range_key": "rank",
    },
    "daily_top_genres": {
        "hash_key": "metric_date",
        "range_key": "rank",
    },
    "pipeline_audit": {
        "hash_key": "execution_id",
        "range_key": "event_ts",
    },
}
