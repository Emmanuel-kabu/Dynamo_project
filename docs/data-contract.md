# Data Contract

## Source Datasets

### Songs

Path: `raw/songs/songs.csv`

Required columns:

| Column | Type | Notes |
| --- | --- | --- |
| `track_id` | string | Natural key for the song catalog. |
| `artists` | string | Artist names. |
| `album_name` | string | Album name. |
| `track_name` | string | Track title. |
| `duration_ms` | integer | Used to compute listening time. |
| `track_genre` | string | Genre dimension. |

### Users

Path: `raw/users/users.csv`

Required columns:

| Column | Type | Notes |
| --- | --- | --- |
| `user_id` | integer/string | Natural key for the user dimension. |
| `user_country` | string | Optional segmentation attribute for future products. |
| `created_at` | date | User creation date. |

### Streams

Path: `raw/streams/<yyyy>/<mm>/<dd>/<file>.csv`

Required columns:

| Column | Type | Notes |
| --- | --- | --- |
| `user_id` | integer/string | Must exist in users. |
| `track_id` | string | Must exist in songs. |
| `listen_time` | timestamp | Event timestamp used to derive metric date. |

## Integrity Pillars

| Pillar | Checks | Failure Action |
| --- | --- | --- |
| Completeness | Required columns exist; critical fields are non-null. | Reject batch and write validation report. |
| Uniqueness | Songs are unique by `track_id`; users are unique by `user_id`; duplicate stream events are counted and reported. | Reject dimension violations; report stream duplicates. |
| Validity | Timestamps parse; ages and durations are positive; audio feature ranges are valid when present. | Reject invalid batch. |
| Consistency | Stream `user_id` and `track_id` exist in reference datasets; metric dates match the input event date when provided. | Reject invalid batch. |
| Timeliness | Stream events are not in the future and are within the configured late-arrival window. | Reject or quarantine based on threshold. |
| Accuracy | KPI reconciliation confirms aggregate listen counts equal accepted stream count; listening duration is sourced from catalog `duration_ms`. | Reject publish if reconciliation fails. |

## Accepted Batch Definition

A stream batch is publishable only when:

1. The stream file, users file, and songs file are readable.
2. Required columns are present.
3. Critical null rates are zero for keys and event timestamp.
4. Invalid type/range counts are zero.
5. Referential integrity failures are zero.
6. KPI reconciliation succeeds after transformation.

## Validation Report

Every validation run writes JSON to:

```text
validation/reports/<execution_id>/validation_report.json
```

Report shape:

```json
{
  "execution_id": "20260705T224000Z-abc123",
  "status": "PASS",
  "source": {
    "bucket": "example",
    "stream_key": "raw/streams/2024/06/25/streams1.csv"
  },
  "metrics": {
    "streams": {"row_count": 11346},
    "songs": {"row_count": 89741},
    "users": {"row_count": 50000}
  },
  "checks": [
    {
      "pillar": "completeness",
      "name": "streams_required_columns",
      "status": "PASS",
      "observed": 0,
      "threshold": 0
    }
  ],
  "failed_checks": []
}
```

## Schema Evolution

The pipeline treats new nullable columns as backward compatible. Removing or renaming required columns is breaking and routes the batch to DLQ. New data products should be introduced with new DynamoDB entities or tables rather than overloading existing keys.
