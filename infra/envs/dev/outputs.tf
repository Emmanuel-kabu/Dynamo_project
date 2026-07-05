output "data_bucket_name" {
  description = "Data lake bucket name."
  value       = module.storage.data_bucket_name
}

output "artifacts_bucket_name" {
  description = "Glue artifact bucket name."
  value       = module.storage.artifacts_bucket_name
}

output "dynamodb_table_names" {
  description = "DynamoDB serving table names."
  value       = module.dynamodb.table_names
}

output "pipeline_dlq_url" {
  description = "Pipeline SQS DLQ URL."
  value       = module.dlq.queue_url
}

output "glue_role_arn" {
  description = "Glue execution role ARN."
  value       = module.iam.glue_role_arn
}

output "step_functions_role_arn" {
  description = "Step Functions execution role ARN."
  value       = module.iam.step_functions_role_arn
}

output "glue_job_names" {
  description = "Glue job names keyed by logical job."
  value       = module.glue.job_names
}

output "state_machine_arn" {
  description = "Pipeline state machine ARN."
  value       = module.step_functions.state_machine_arn
}

output "eventbridge_rule_name" {
  description = "EventBridge S3 trigger rule name."
  value       = module.eventbridge.rule_name
}
