variable "aws_account_id" {
  description = "AWS account allowed for this environment."
  type        = string
  default     = "831926601640"
}

variable "aws_region" {
  description = "AWS region for the pipeline."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used in resource names."
  type        = string
  default     = "dynamo-music-streaming"
}

variable "environment" {
  description = "Deployment environment name."
  type        = string
  default     = "dev"
}

variable "late_arrival_days" {
  description = "Maximum accepted age for stream events before they are quarantined."
  type        = number
  default     = 1095
}
