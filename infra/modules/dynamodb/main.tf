locals {
  tables = {
    daily_genre_kpis = {
      name_suffix = "daily-genre-kpis"
      hash_key    = "metric_date"
      range_key   = "genre"
      attributes = {
        metric_date = "S"
        genre       = "S"
      }
    }
    daily_genre_top_songs = {
      name_suffix = "daily-genre-top-songs"
      hash_key    = "metric_date_genre"
      range_key   = "rank"
      attributes = {
        metric_date_genre = "S"
        rank              = "N"
      }
    }
    daily_top_genres = {
      name_suffix = "daily-top-genres"
      hash_key    = "metric_date"
      range_key   = "rank"
      attributes = {
        metric_date = "S"
        rank        = "N"
      }
    }
    pipeline_audit = {
      name_suffix = "pipeline-audit"
      hash_key    = "execution_id"
      range_key   = "event_ts"
      attributes = {
        execution_id = "S"
        event_ts     = "S"
      }
    }
  }
}

resource "aws_dynamodb_table" "this" {
  for_each = local.tables

  name         = "${var.name_prefix}-${each.value.name_suffix}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = each.value.hash_key
  range_key    = each.value.range_key

  dynamic "attribute" {
    for_each = each.value.attributes

    content {
      name = attribute.key
      type = attribute.value
    }
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }

  tags = var.tags
}
