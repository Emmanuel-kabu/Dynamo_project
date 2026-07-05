# Deployment Guide

## Prerequisites

- AWS account: `831926601640`
- Terraform 1.6+
- AWS CLI v2 authenticated with an operator role
- Python 3.10+ for local tests

Do not place AWS access keys in Terraform variables, code, or committed files. Use SSO, environment credentials managed outside the repository, or an assumed role.

## Configure Terraform

```powershell
cd infra/envs/dev
terraform init
terraform plan -var="aws_account_id=831926601640"
terraform apply -var="aws_account_id=831926601640"
```

Important variables:

| Variable | Purpose |
| --- | --- |
| `aws_account_id` | Deployment account guardrail. |
| `aws_region` | Target region. Defaults to `us-east-1`. |
| `project_name` | Resource naming prefix. |
| `environment` | Environment suffix such as `dev`. |
| `late_arrival_days` | Maximum accepted stream event age. |

## Package And Upload Glue Assets

Terraform uploads the Glue scripts from `src/glue/jobs` and `src/glue/lib` to the artifact S3 bucket. If you change scripts after deployment, rerun `terraform apply`.

## Upload Source Data

```powershell
aws s3 cp data/songs/songs.csv s3://<data-bucket>/raw/songs/songs.csv
aws s3 cp data/users/users.csv s3://<data-bucket>/raw/users/users.csv
aws s3 cp data/streams/streams1.csv s3://<data-bucket>/raw/streams/2024/06/25/streams1.csv
```

Each new object under `raw/streams/` starts the state machine through EventBridge.

## Manual Replay

```powershell
aws stepfunctions start-execution `
  --state-machine-arn <state-machine-arn> `
  --input '{"bucket":"<data-bucket>","key":"raw/streams/2024/06/25/streams1.csv"}'
```

## DynamoDB Query Examples

Daily genre KPIs:

```powershell
aws dynamodb query `
  --table-name <prefix>-daily-genre-kpis `
  --key-condition-expression "metric_date = :d" `
  --expression-attribute-values '{":d":{"S":"2024-06-25"}}'
```

Top songs for a genre:

```powershell
aws dynamodb query `
  --table-name <prefix>-daily-genre-top-songs `
  --key-condition-expression "metric_date_genre = :g" `
  --expression-attribute-values '{":g":{"S":"2024-06-25#acoustic"}}' `
  --limit 3
```

Top genres:

```powershell
aws dynamodb query `
  --table-name <prefix>-daily-top-genres `
  --key-condition-expression "metric_date = :d" `
  --expression-attribute-values '{":d":{"S":"2024-06-25"}}' `
  --limit 5
```
