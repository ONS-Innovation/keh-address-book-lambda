# The Process

1. Authenticate with GitHub via GitHub App credentials (env vars).
2. Query the organisation members via GraphQL using `github-api-toolkit`.
3. Build username↔email mappings and username→id mapping.
4. Write three JSON files to the configured S3 bucket under `AddressBook/`.
5. Log progress and errors; failures surface in CloudWatch.

See [Configuration](configuration.md) for required environment variables.

## Detailed Steps

- Initialise logging and read required environment variables.
- Establish GitHub App authentication and create GraphQL requests (via `github-api-toolkit`).
- Retrieve organisation members and their verified organisation email addresses and account IDs, using pagination.
- Build three dictionaries:
  - username → list of verified org emails
  - email → username
  - username → GitHub account ID
- Convert the dictionaries to JSON.
- Write JSON files to S3 under the `AddressBook/` prefix.

## Key Components

- `src/lambda_function.py`: Orchestrates the run and calls downstream helpers.
- `src/github_services.py`: Handles GitHub GraphQL interactions via `github-api-toolkit`.
- `src/s3writer.py`: Writes JSON outputs to S3.
- `src/logger.py`: Provides structured logging.

## Error Handling & Observability

- All major steps are logged; inspect CloudWatch Logs for failures or anomalies.
- Ensure the Lambda role has `s3:PutObject` to the target bucket/prefix; access issues will surface during S3 writes.
- Verify GitHub App installation and credentials if API calls fail.

## Outputs

- Files are written to S3 under the `AddressBook/` prefix:
  - `addressBookUsernameKey.json`
  - `addressBookEmailKey.json`
  - `addressBookIDKey.json`

Return to the overview: [Overview](overview.md) or dive deeper into configuration: [Configuration](configuration.md).
