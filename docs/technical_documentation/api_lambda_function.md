# Lambda Handler (API)

The Lambda handler controls the address book run: reads configuration and credentials, authenticates to GitHub, gathers user details, writes three JSON lookup files to S3, and sends Teams notifications.

## Overview

- Reads env vars: `GITHUB_ORG`, `S3_BUCKET_NAME`, `GITHUB_CLIENT_ID_SECRET_NAME`, `GITHUB_PRIVATE_KEY_SECRET_NAME`, and `ALERT_SECRET_NAME`.
- Creates Boto3 clients for Secrets Manager and S3.
- Reads the GitHub client ID from the `ClientID` field in the client ID secret JSON. The private-key secret contains the PEM text as its secret string.
- Reads the alert secret as JSON with `azure_tenant_id`, `azure_client_id`, `azure_client_secret`, `azure_webhook_url`, and `channel_id` fields.
- Uses `GitHubServices.get_all_user_details()` to retrieve:
  - username → verified org emails
  - email → username
  - username → GitHub account ID
- Writes JSON outputs under `AddressBook/` prefix to the configured S3 bucket.
- Sends a Teams success notification after all files are written. It sends error notifications when fetching GitHub data or writing to S3 fails.
- Logs progress and errors via `wrapped_logging`.

## Local Run (development)

```bash
export GITHUB_ORG=<org>
export S3_BUCKET_NAME=<bucket_name>
export GITHUB_CLIENT_ID_SECRET_NAME=<github_client_id_secret_name>
export GITHUB_PRIVATE_KEY_SECRET_NAME=<github_private_key_secret_name>
export ALERT_SECRET_NAME=<alert_secret_name>

poetry run python3 src/lambda_function.py
```

The AWS identity used locally must be allowed to read all three secrets and write to the target S3 bucket.

## Responses

- 200: success with `user_entries` count
- 404: organisation not found
- Exceptions (reported by Lambda as a failed invocation): missing configuration or credentials, GitHub query failure, or S3 write failure

## Reference

::: lambda_function
