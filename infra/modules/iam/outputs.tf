output "glue_role_arn" {
  description = "Glue execution role ARN."
  value       = aws_iam_role.glue.arn
}

output "step_functions_role_arn" {
  description = "Step Functions execution role ARN."
  value       = aws_iam_role.step_functions.arn
}

output "eventbridge_role_arn" {
  description = "EventBridge target role ARN."
  value       = aws_iam_role.eventbridge.arn
}

output "eventbridge_role_name" {
  description = "EventBridge target role name."
  value       = aws_iam_role.eventbridge.name
}
