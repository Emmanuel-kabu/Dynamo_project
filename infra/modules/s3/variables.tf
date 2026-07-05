variable "name_prefix" {
  description = "Resource name prefix."
  type        = string
}

variable "aws_account_id" {
  description = "AWS account id used in globally unique bucket names."
  type        = string
}

variable "aws_region" {
  description = "AWS region used in globally unique bucket names."
  type        = string
}

variable "tags" {
  description = "Tags applied to all resources."
  type        = map(string)
  default     = {}
}
