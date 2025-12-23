# Lambda Handler (API)

The Lambda handler controls the address book run: reads configuration, authenticates to GitHub, gathers user details, and writes three JSON lookup files to S3.

## Overview

- Reads env vars: `GITHUB_ORG`, `AWS_SECRET_NAME`, `GITHUB_APP_CLIENT_ID`, `S3_BUCKET_NAME`.
- Creates Boto3 clients for Secrets Manager and S3.
- Uses `GitHubServices.get_all_user_details()` to retrieve:
	- username → verified org emails
	- email → username
	- username → GitHub account ID
- Writes JSON outputs under `AddressBook/` prefix to the configured S3 bucket.
- Logs progress and errors via `wrapped_logging`.

## Local Run (development)

```bash
export GITHUB_ORG=<org>
export AWS_SECRET_NAME=<secret_name>
export GITHUB_APP_CLIENT_ID=<client_id>
export S3_BUCKET_NAME=<bucket_name>
export AWS_ACCESS_KEY_ID=<access_key>
export AWS_SECRET_ACCESS_KEY=<secret_key>

poetry run python3 src/lambda_function.py
```

## Responses

- 200: success with `user_entries` count
- 404: organisation not found
- 500: missing configuration or S3 write failure

## Reference

::: lambda_function
