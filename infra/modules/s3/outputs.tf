output "data_bucket_name" {
  description = "Data lake bucket name."
  value       = aws_s3_bucket.this["data"].id
}

output "data_bucket_arn" {
  description = "Data lake bucket ARN."
  value       = aws_s3_bucket.this["data"].arn
}

output "artifacts_bucket_name" {
  description = "Glue artifact bucket name."
  value       = aws_s3_bucket.this["artifacts"].id
}

output "artifacts_bucket_arn" {
  description = "Glue artifact bucket ARN."
  value       = aws_s3_bucket.this["artifacts"].arn
}

output "bucket_arns" {
  description = "All bucket ARNs managed by the module."
  value       = [for bucket in aws_s3_bucket.this : bucket.arn]
}
