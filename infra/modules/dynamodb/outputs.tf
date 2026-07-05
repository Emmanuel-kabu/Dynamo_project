output "table_names" {
  description = "DynamoDB table names keyed by data product."
  value       = { for key, table in aws_dynamodb_table.this : key => table.name }
}

output "table_arns" {
  description = "DynamoDB table ARNs keyed by data product."
  value       = { for key, table in aws_dynamodb_table.this : key => table.arn }
}
