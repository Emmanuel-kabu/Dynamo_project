# Semantic Layer And Data Products

## Design Principles

- Data products are shaped for downstream application access patterns.
- Metrics use stable names and deterministic keys.
- DynamoDB records include `metric_date`, `data_product`, `version`, `generated_at`, and `source_execution_id`.
- PII fields are not published to serving tables.

## Metric Definitions

| Metric | Definition |
| --- | --- |
| `listen_count` | Count of accepted stream events for a genre on a metric date. |
| `unique_listeners` | Distinct `user_id` count for a genre on a metric date. |
| `total_listening_time_ms` | Sum of song `duration_ms` for accepted streams in the genre/date. |
| `avg_listening_time_ms_per_user` | `total_listening_time_ms / unique_listeners`. |
| `top_3_songs_per_genre` | Songs ranked by stream count within genre/date; tie-breakers are `track_name`, then `track_id`. |
| `top_5_genres_per_day` | Genres ranked by `listen_count` within date; tie-breaker is `track_genre`. |

## Data Product: Daily Genre KPIs

Table: `daily_genre_kpis`

| Key | Value |
| --- | --- |
| Partition key | `metric_date` |
| Sort key | `genre` |

Attributes:

```json
{
  "metric_date": "2024-06-25",
  "genre": "acoustic",
  "listen_count": 123,
  "unique_listeners": 119,
  "total_listening_time_ms": 24567890,
  "avg_listening_time_ms_per_user": 206452.86,
  "generated_at": "2026-07-05T22:40:00Z",
  "source_execution_id": "20260705T224000Z-abc123",
  "version": 1
}
```

Primary access pattern:

```text
Get all genre metrics for a day:
PK metric_date = "2024-06-25"
```

## Data Product: Daily Genre Top Songs

Table: `daily_genre_top_songs`

| Key | Value |
| --- | --- |
| Partition key | `metric_date_genre` formatted as `<yyyy-mm-dd>#<genre>` |
| Sort key | `rank` numeric |

Attributes:

```json
{
  "metric_date_genre": "2024-06-25#acoustic",
  "rank": 1,
  "metric_date": "2024-06-25",
  "genre": "acoustic",
  "track_id": "5SuOikwiRyPMVoIQDJUgSV",
  "track_name": "Comedy",
  "artists": "Gen Hoshino",
  "listen_count": 42,
  "generated_at": "2026-07-05T22:40:00Z",
  "source_execution_id": "20260705T224000Z-abc123",
  "version": 1
}
```

Primary access pattern:

```text
Get top songs for a genre/day:
PK metric_date_genre = "2024-06-25#acoustic"
Limit 3
```

## Data Product: Daily Top Genres

Table: `daily_top_genres`

| Key | Value |
| --- | --- |
| Partition key | `metric_date` |
| Sort key | `rank` numeric |

Attributes:

```json
{
  "metric_date": "2024-06-25",
  "rank": 1,
  "genre": "acoustic",
  "listen_count": 123,
  "unique_listeners": 119,
  "generated_at": "2026-07-05T22:40:00Z",
  "source_execution_id": "20260705T224000Z-abc123",
  "version": 1
}
```

Primary access pattern:

```text
Get top genres for a day:
PK metric_date = "2024-06-25"
Limit 5
```

## Versioning

Version `1` is the initial semantic contract. Breaking changes require either a new `version` value with dual publishing or a new table/data-product name.
