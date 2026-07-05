output "queue_arn" {
  description = "Pipeline DLQ ARN."
  value       = aws_sqs_queue.pipeline_dlq.arn
}

output "queue_url" {
  description = "Pipeline DLQ URL."
  value       = aws_sqs_queue.pipeline_dlq.url
}

output "queue_name" {
  description = "Pipeline DLQ name."
  value       = aws_sqs_queue.pipeline_dlq.name
}
