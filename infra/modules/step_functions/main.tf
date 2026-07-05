resource "aws_cloudwatch_log_group" "state_machine" {
  name              = "/aws/vendedlogs/states/${var.name_prefix}-pipeline"
  retention_in_days = 30
  tags              = var.tags
}

resource "aws_sfn_state_machine" "pipeline" {
  name     = "${var.name_prefix}-pipeline"
  role_arn = var.state_machine_role_arn

  definition = templatefile("${path.module}/state_machine.asl.json.tftpl", {
    validate_job_name           = var.glue_job_names["validate_stream_batch"]
    compute_job_name            = var.glue_job_names["compute_daily_kpis"]
    publish_job_name            = var.glue_job_names["publish_to_dynamodb"]
    dlq_queue_url               = var.dlq_queue_url
    late_arrival_days           = var.late_arrival_days
    daily_genre_kpis_table      = var.dynamodb_table_names["daily_genre_kpis"]
    daily_genre_top_songs_table = var.dynamodb_table_names["daily_genre_top_songs"]
    daily_top_genres_table      = var.dynamodb_table_names["daily_top_genres"]
    pipeline_audit_table        = var.dynamodb_table_names["pipeline_audit"]
  })

  logging_configuration {
    include_execution_data = true
    level                  = "ERROR"
    log_destination        = "${aws_cloudwatch_log_group.state_machine.arn}:*"
  }

  tracing_configuration {
    enabled = true
  }

  tags = var.tags
}
