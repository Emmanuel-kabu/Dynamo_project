# Operations Runbook

## Normal Processing

1. A stream CSV lands under `raw/streams/`.
2. EventBridge starts the Step Functions workflow.
3. Validation writes a report to `validation/reports/<execution_id>/`.
4. KPI transformation writes curated JSON to `curated/`.
5. DynamoDB publisher upserts serving records.
6. The raw stream file is copied to `archive/` and removed from the active raw prefix.

## Validation Failure

Symptoms:

- Step Functions execution fails at or immediately after validation.
- SQS DLQ has a message with `failure_type = "VALIDATION"`.
- S3 contains a validation report with failed checks.
- The rejected source object is copied to `dlq/streams/<execution_id>/`.

Response:

1. Read the validation report.
2. Correct the upstream file or reference dataset.
3. Upload a corrected object under `raw/streams/`.
4. Keep the DLQ copy for audit unless retention policy says otherwise.

## Technical Failure

Symptoms:

- Step Functions catch path sends a message to SQS DLQ.
- Glue job logs contain exceptions unrelated to data quality.

Response:

1. Inspect the SQS DLQ message for `execution_arn`, `state`, `error`, and `cause`.
2. Inspect CloudWatch logs for the failed Glue job.
3. Fix configuration, permissions, or code.
4. Replay the original state machine input.

## Replay Safety

Replays are safe because DynamoDB keys are deterministic for each metric date, genre, rank, and track. A replay overwrites the same logical records with a newer `generated_at` and `source_execution_id`.

## Monitoring

Recommended alarms:

- Step Functions executions failed >= 1 in 15 minutes.
- Glue job failed >= 1 in 15 minutes.
- SQS DLQ visible messages >= 1.
- DynamoDB throttled requests > 0.
- S3 validation failures count > 0 for expected production windows.

## Data Product Consumer Notes

Downstream applications should read only from DynamoDB serving tables. S3 curated outputs are analytical/audit artifacts and may be reorganized independently as long as the DynamoDB semantic contract is preserved.
