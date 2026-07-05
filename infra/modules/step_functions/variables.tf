variable "name_prefix" {
  description = "Resource name prefix."
  type        = string
}

variable "state_machine_role_arn" {
  description = "Step Functions execution role ARN."
  type        = string
}

variable "glue_job_names" {
  description = "Glue job names keyed by logical job."
  type        = map(string)
}

variable "data_bucket_name" {
  description = "Data lake bucket name."
  type        = string
}

variable "dlq_queue_url" {
  description = "SQS DLQ queue URL."
  type        = string
}

variable "dynamodb_table_names" {
  description = "DynamoDB table names keyed by logical data product."
  type        = map(string)
}

variable "late_arrival_days" {
  description = "Maximum accepted late arrival window."
  type        = number
}

variable "tags" {
  description = "Tags applied to all resources."
  type        = map(string)
  default     = {}
}
