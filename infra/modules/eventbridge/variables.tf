variable "name_prefix" {
  description = "Resource name prefix."
  type        = string
}

variable "data_bucket_name" {
  description = "S3 data bucket that emits object-created events."
  type        = string
}

variable "state_machine_arn" {
  description = "Target Step Functions state machine ARN."
  type        = string
}

variable "eventbridge_role_arn" {
  description = "EventBridge target role ARN."
  type        = string
}

variable "eventbridge_role_name" {
  description = "EventBridge target role name."
  type        = string
}

variable "tags" {
  description = "Tags applied to all resources."
  type        = map(string)
  default     = {}
}
