locals {
  scripts = {
    validate_stream_batch = "${var.project_root}/src/glue/jobs/validate_stream_batch.py"
    compute_daily_kpis    = "${var.project_root}/src/glue/jobs/compute_daily_kpis.py"
    publish_to_dynamodb   = "${var.project_root}/src/glue/jobs/publish_to_dynamodb.py"
  }

  default_spark_arguments = {
    "--enable-continuous-cloudwatch-log" = "true"
    "--enable-glue-datacatalog"          = "true"
    "--enable-job-insights"              = "true"
    "--enable-metrics"                   = "true"
    "--enable-observability-metrics"     = "true"
    "--enable-spark-ui"                  = "true"
    "--extra-py-files"                   = "s3://${var.artifacts_bucket_name}/${aws_s3_object.shared_lib.key}"
    "--job-language"                     = "python"
    "--TempDir"                          = "s3://${var.artifacts_bucket_name}/glue/temp/"
    "--spark-event-logs-path"            = "s3://${var.artifacts_bucket_name}/glue/spark-history/"
  }
}

data "archive_file" "shared_lib" {
  type        = "zip"
  source_dir  = "${var.project_root}/src/glue/lib"
  output_path = "${path.module}/music_etl_lib.zip"
}

resource "aws_s3_object" "scripts" {
  for_each = local.scripts

  bucket       = var.artifacts_bucket_name
  key          = "glue/scripts/${basename(each.value)}"
  source       = each.value
  source_hash  = filemd5(each.value)
  content_type = "text/x-python"
  tags         = var.tags
}

resource "aws_s3_object" "shared_lib" {
  bucket      = var.artifacts_bucket_name
  key         = "glue/lib/music_etl_lib.zip"
  source      = data.archive_file.shared_lib.output_path
  source_hash = data.archive_file.shared_lib.output_base64sha256
  tags        = var.tags
}

resource "aws_glue_job" "validate_stream_batch" {
  name              = "${var.name_prefix}-validate-stream-batch"
  role_arn          = var.glue_role_arn
  glue_version      = "4.0"
  worker_type       = "G.1X"
  number_of_workers = 2
  timeout           = 30

  command {
    name            = "glueetl"
    script_location = "s3://${var.artifacts_bucket_name}/${aws_s3_object.scripts["validate_stream_batch"].key}"
    python_version  = "3"
  }

  default_arguments = local.default_spark_arguments
  tags              = var.tags
}

resource "aws_glue_job" "compute_daily_kpis" {
  name              = "${var.name_prefix}-compute-daily-kpis"
  role_arn          = var.glue_role_arn
  glue_version      = "4.0"
  worker_type       = "G.1X"
  number_of_workers = 2
  timeout           = 30

  command {
    name            = "glueetl"
    script_location = "s3://${var.artifacts_bucket_name}/${aws_s3_object.scripts["compute_daily_kpis"].key}"
    python_version  = "3"
  }

  default_arguments = local.default_spark_arguments
  tags              = var.tags
}

resource "aws_glue_job" "publish_to_dynamodb" {
  name         = "${var.name_prefix}-publish-to-dynamodb"
  role_arn     = var.glue_role_arn
  glue_version = "3.0"
  max_capacity = 0.0625
  timeout      = 15

  command {
    name            = "pythonshell"
    script_location = "s3://${var.artifacts_bucket_name}/${aws_s3_object.scripts["publish_to_dynamodb"].key}"
    python_version  = "3.9"
  }

  default_arguments = {
    "--extra-py-files" = "s3://${var.artifacts_bucket_name}/${aws_s3_object.shared_lib.key}"
    "--job-language"   = "python"
  }

  tags = var.tags
}
