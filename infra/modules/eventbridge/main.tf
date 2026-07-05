resource "aws_iam_role_policy" "start_pipeline" {
  name = "${var.name_prefix}-eventbridge-start-pipeline"
  role = var.eventbridge_role_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "StartPipelineExecution"
        Effect   = "Allow"
        Action   = ["states:StartExecution"]
        Resource = var.state_machine_arn
      }
    ]
  })
}

resource "aws_cloudwatch_event_rule" "stream_object_created" {
  name        = "${var.name_prefix}-stream-object-created"
  description = "Start the streaming KPI pipeline when a stream CSV lands in S3."

  event_pattern = jsonencode({
    source        = ["aws.s3"]
    "detail-type" = ["Object Created"]
    detail = {
      bucket = {
        name = [var.data_bucket_name]
      }
      object = {
        key = [
          {
            prefix = "raw/streams/"
          }
        ]
      }
    }
  })

  tags = var.tags
}

resource "aws_cloudwatch_event_target" "pipeline" {
  rule      = aws_cloudwatch_event_rule.stream_object_created.name
  target_id = "${var.name_prefix}-pipeline"
  arn       = var.state_machine_arn
  role_arn  = var.eventbridge_role_arn

  input_transformer {
    input_paths = {
      bucket = "$.detail.bucket.name"
      key    = "$.detail.object.key"
    }

    input_template = "{\"bucket\":\"<bucket>\",\"key\":\"<key>\"}"
  }
}
