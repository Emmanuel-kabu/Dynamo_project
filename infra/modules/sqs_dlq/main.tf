resource "aws_sqs_queue" "pipeline_dlq" {
  name                       = "${var.name_prefix}-pipeline-dlq"
  message_retention_seconds  = 1209600
  visibility_timeout_seconds = 300
  sqs_managed_sse_enabled    = true

  tags = var.tags
}
