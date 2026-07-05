output "rule_name" {
  description = "EventBridge rule name."
  value       = aws_cloudwatch_event_rule.stream_object_created.name
}
