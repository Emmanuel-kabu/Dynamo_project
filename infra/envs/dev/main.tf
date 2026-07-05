module "storage" {
  source = "../../modules/s3"

  name_prefix    = local.name_prefix
  aws_account_id = var.aws_account_id
  aws_region     = var.aws_region
  tags           = local.tags
}

module "dynamodb" {
  source = "../../modules/dynamodb"

  name_prefix = local.name_prefix
  tags        = local.tags
}

module "dlq" {
  source = "../../modules/sqs_dlq"

  name_prefix = local.name_prefix
  tags        = local.tags
}

module "iam" {
  source = "../../modules/iam"

  name_prefix         = local.name_prefix
  aws_account_id      = var.aws_account_id
  aws_region          = var.aws_region
  bucket_arns         = module.storage.bucket_arns
  dynamodb_table_arns = module.dynamodb.table_arns
  dlq_queue_arn       = module.dlq.queue_arn
  tags                = local.tags
}

module "glue" {
  source = "../../modules/glue"

  name_prefix           = local.name_prefix
  project_root          = local.project_root
  artifacts_bucket_name = module.storage.artifacts_bucket_name
  glue_role_arn         = module.iam.glue_role_arn
  tags                  = local.tags
}

module "step_functions" {
  source = "../../modules/step_functions"

  name_prefix            = local.name_prefix
  state_machine_role_arn = module.iam.step_functions_role_arn
  glue_job_names         = module.glue.job_names
  data_bucket_name       = module.storage.data_bucket_name
  dlq_queue_url          = module.dlq.queue_url
  dynamodb_table_names   = module.dynamodb.table_names
  late_arrival_days      = var.late_arrival_days
  tags                   = local.tags
}

module "eventbridge" {
  source = "../../modules/eventbridge"

  name_prefix           = local.name_prefix
  data_bucket_name      = module.storage.data_bucket_name
  state_machine_arn     = module.step_functions.state_machine_arn
  eventbridge_role_arn  = module.iam.eventbridge_role_arn
  eventbridge_role_name = module.iam.eventbridge_role_name
  tags                  = local.tags
}
