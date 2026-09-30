# The Process

1. Read GitHub and Teams credentials from AWS Secrets Manager using the configured secret-name environment variables.
2. Query the organisation members via GraphQL using `github-api-toolkit`.
3. Build username↔email mappings and username→id mapping.
4. Write three JSON files to the configured S3 bucket under `AddressBook/`.
5. Send a Teams success notification, or send a Teams error notification if fetching GitHub data or writing to S3 fails. Log progress and errors to CloudWatch.

See [Configuration](configuration.md) for required environment variables.

## Detailed Steps

- Initialise logging and read required environment variables: `GITHUB_ORG`, `S3_BUCKET_NAME`, `GITHUB_CLIENT_ID_SECRET_NAME`, `GITHUB_PRIVATE_KEY_SECRET_NAME`, and `ALERT_SECRET_NAME`.
- Read the GitHub client ID (`ClientID` in a JSON secret) and private-key PEM from Secrets Manager. Read the Teams alert secret JSON, which must contain `azure_tenant_id`, `azure_client_id`, `azure_client_secret`, `azure_webhook_url`, and `channel_id`.
- Establish GitHub App authentication and create GraphQL requests (via `github-api-toolkit`).
- Retrieve organisation members and their verified organisation email addresses and account IDs, using pagination.
- Build three dictionaries:
  - username → list of verified org emails
  - email → username
  - username → GitHub account ID
- Convert the dictionaries to JSON.
- Write JSON files to S3 under the `AddressBook/` prefix.
- Send a Teams success notification with the number of users after all S3 writes complete. On GitHub fetch or S3 write exceptions, send an error notification and re-raise the exception.

## Key Components

- `src/lambda_function.py`: Orchestrates the run and calls downstream helpers.
- `src/github_services.py`: Handles GitHub GraphQL interactions via `github-api-toolkit`.
- `src/s3writer.py`: Writes JSON outputs to S3.
- `src/logger.py`: Provides structured logging.

## Error Handling & Observability

- All major steps are logged; inspect CloudWatch Logs for failures or anomalies.
- Ensure the Lambda role has `s3:PutObject` to the target bucket/prefix; access issues will surface during S3 writes.
- Ensure the Lambda role can read each configured GitHub and alert secret, and that the Teams credentials and webhook/channel values are valid.
- Verify GitHub App installation and credentials if API calls fail.

## Outputs

- Files are written to S3 under the `AddressBook/` prefix:
  - `addressBookUsernameKey.json`
  - `addressBookEmailKey.json`
  - `addressBookIDKey.json`

Return to the overview: [Overview](overview.md) or dive deeper into configuration: [Configuration](configuration.md).
