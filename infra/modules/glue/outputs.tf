output "job_names" {
  description = "Glue job names keyed by logical job."
  value = {
    validate_stream_batch = aws_glue_job.validate_stream_batch.name
    compute_daily_kpis    = aws_glue_job.compute_daily_kpis.name
    publish_to_dynamodb   = aws_glue_job.publish_to_dynamodb.name
  }
}

output "script_object_keys" {
  description = "Uploaded Glue script object keys."
  value       = { for key, object in aws_s3_object.scripts : key => object.key }
}
