variable "name_prefix" {
  description = "Resource name prefix."
  type        = string
}

variable "project_root" {
  description = "Absolute project root used to locate source files."
  type        = string
}

variable "artifacts_bucket_name" {
  description = "S3 bucket for Glue scripts and libraries."
  type        = string
}

variable "glue_role_arn" {
  description = "Glue execution role ARN."
  type        = string
}

variable "tags" {
  description = "Tags applied to all resources."
  type        = map(string)
  default     = {}
}
