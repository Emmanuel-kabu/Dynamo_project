locals {
  bucket_object_arns = [for arn in var.bucket_arns : "${arn}/*"]
  glue_job_arn       = "arn:aws:glue:${var.aws_region}:${var.aws_account_id}:job/${var.name_prefix}-*"
}

data "aws_iam_policy_document" "glue_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["glue.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "glue" {
  name               = "${var.name_prefix}-glue-role"
  assume_role_policy = data.aws_iam_policy_document.glue_assume_role.json
  tags               = var.tags
}

resource "aws_iam_role_policy_attachment" "glue_service_role" {
  role       = aws_iam_role.glue.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

resource "aws_iam_role_policy" "glue_pipeline_access" {
  name = "${var.name_prefix}-glue-pipeline-access"
  role = aws_iam_role.glue.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "S3DataLakeAccess"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket",
          "s3:GetBucketLocation"
        ]
        Resource = concat(var.bucket_arns, local.bucket_object_arns)
      },
      {
        Sid    = "DynamoDbPublishAccess"
        Effect = "Allow"
        Action = [
          "dynamodb:BatchWriteItem",
          "dynamodb:DescribeTable",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem"
        ]
        Resource = values(var.dynamodb_table_arns)
      },
      {
        Sid      = "DlqSendAccess"
        Effect   = "Allow"
        Action   = ["sqs:SendMessage"]
        Resource = var.dlq_queue_arn
      }
    ]
  })
}

data "aws_iam_policy_document" "states_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["states.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "step_functions" {
  name               = "${var.name_prefix}-step-functions-role"
  assume_role_policy = data.aws_iam_policy_document.states_assume_role.json
  tags               = var.tags
}

resource "aws_iam_role_policy" "step_functions_pipeline_access" {
  name = "${var.name_prefix}-step-functions-pipeline-access"
  role = aws_iam_role.step_functions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "GlueJobOrchestration"
        Effect = "Allow"
        Action = [
          "glue:StartJobRun",
          "glue:GetJobRun",
          "glue:GetJobRuns",
          "glue:BatchStopJobRun"
        ]
        Resource = local.glue_job_arn
      },
      {
        Sid    = "S3ArchiveAndQuarantine"
        Effect = "Allow"
        Action = [
          "s3:DeleteObject",
          "s3:GetObject",
          "s3:GetObjectVersion",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = concat(var.bucket_arns, local.bucket_object_arns)
      },
      {
        Sid      = "SendDlqMessages"
        Effect   = "Allow"
        Action   = ["sqs:SendMessage"]
        Resource = var.dlq_queue_arn
      },
      {
        Sid      = "PassGlueRole"
        Effect   = "Allow"
        Action   = ["iam:PassRole"]
        Resource = aws_iam_role.glue.arn
        Condition = {
          StringEquals = {
            "iam:PassedToService" = "glue.amazonaws.com"
          }
        }
      },
      {
        Sid    = "StepFunctionsLogDelivery"
        Effect = "Allow"
        Action = [
          "logs:CreateLogDelivery",
          "logs:GetLogDelivery",
          "logs:UpdateLogDelivery",
          "logs:DeleteLogDelivery",
          "logs:ListLogDeliveries",
          "logs:PutResourcePolicy",
          "logs:DescribeResourcePolicies",
          "logs:DescribeLogGroups"
        ]
        Resource = "*"
      },
      {
        Sid    = "StepFunctionsSyncEventBridgeRule"
        Effect = "Allow"
        Action = [
          "events:DeleteRule",
          "events:DescribeRule",
          "events:PutRule",
          "events:PutTargets",
          "events:RemoveTargets"
        ]
        Resource = "arn:aws:events:${var.aws_region}:${var.aws_account_id}:rule/StepFunctionsGetEventsForGlueJobRule"
      },
      {
        Sid    = "StepFunctionsXRayTracing"
        Effect = "Allow"
        Action = [
          "xray:GetSamplingRules",
          "xray:GetSamplingTargets",
          "xray:PutTelemetryRecords",
          "xray:PutTraceSegments"
        ]
        Resource = "*"
      }
    ]
  })
}

data "aws_iam_policy_document" "eventbridge_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["events.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "eventbridge" {
  name               = "${var.name_prefix}-eventbridge-role"
  assume_role_policy = data.aws_iam_policy_document.eventbridge_assume_role.json
  tags               = var.tags
}
