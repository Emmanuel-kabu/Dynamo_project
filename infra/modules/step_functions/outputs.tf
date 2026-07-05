output "state_machine_arn" {
  description = "Pipeline state machine ARN."
  value       = aws_sfn_state_machine.pipeline.arn
}

output "state_machine_name" {
  description = "Pipeline state machine name."
  value       = aws_sfn_state_machine.pipeline.name
}
