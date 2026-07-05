# Dynamo Music Streaming ETL

Production-oriented AWS data pipeline for music streaming events. The design ingests batch files from S3 at irregular intervals, orchestrates validation and transformation with AWS Step Functions, computes daily KPIs in AWS Glue, and publishes low-latency data products to DynamoDB for downstream applications.

## What This Delivers

- Event-driven S3 to Step Functions orchestration.
- Modular Terraform for S3, IAM, Glue, DynamoDB, SQS DLQ, and Step Functions.
- PySpark validation across the six data integrity pillars: completeness, uniqueness, validity, consistency, timeliness, and accuracy.
- DLQ/quarantine path for failed files and failed workflow executions.
- Daily genre KPI and song leaderboard data products optimized for application lookups.
- Semantic layer contract, data product documentation, sample DynamoDB access patterns, and operating runbook.
- Local unit tests for reusable validation helpers.

## Repository Layout

```text
docs/                 Architecture, semantic layer, runbook, deployment notes
infra/                Terraform root and reusable modules
src/glue/jobs/        Glue Python Shell and PySpark jobs
src/glue/lib/         Shared Python helpers packaged for Glue
tests/                Local unit tests and small CSV fixtures
```

The original source CSVs are intentionally ignored by Git. Upload them to the configured raw S3 prefixes during deployment or local testing.

## Quick Start

```powershell
python -m venv .venv
. .venv/Scripts/Activate.ps1
pip install -r requirements-dev.txt
pytest
```

For AWS deployment, see [docs/deployment.md](docs/deployment.md).
