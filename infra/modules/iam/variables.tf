variable "name_prefix" {
  description = "Resource name prefix."
  type        = string
}

variable "aws_account_id" {
  description = "AWS account id."
  type        = string
}

variable "aws_region" {
  description = "AWS region."
  type        = string
}

variable "bucket_arns" {
  description = "S3 bucket ARNs used by the pipeline."
  type        = list(string)
}

variable "dynamodb_table_arns" {
  description = "DynamoDB table ARNs used by the pipeline."
  type        = map(string)
}

variable "dlq_queue_arn" {
  description = "SQS DLQ ARN."
  type        = string
}

variable "tags" {
  description = "Tags applied to all resources."
  type        = map(string)
  default     = {}
}
