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
