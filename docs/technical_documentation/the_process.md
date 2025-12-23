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

## Implementation

For full source see `src/lambda_function.py`. The core logic is:

```python
def lambda_handler(event, context):
    org = os.getenv("GITHUB_ORG")
    secret_name = os.getenv("AWS_SECRET_NAME")
    app_client_id = os.getenv("GITHUB_APP_CLIENT_ID")
    bucket = os.getenv("S3_BUCKET_NAME")

    logger = wrapped_logging(False)
    sm = boto3.client("secretsmanager")
    s3 = boto3.client("s3")

    gh = GitHubServices(org, logger, sm, secret_name, app_client_id)
    s3writer = S3Writer(logger, s3, bucket)

    user_to_email, email_to_user, user_to_id = gh.get_all_user_details()

    prefix = "AddressBook/"
    s3writer.write_data_to_s3(prefix + "addressBookUsernameKey.json", json.dumps(user_to_email))
    s3writer.write_data_to_s3(prefix + "addressBookEmailKey.json", json.dumps(email_to_user))
    s3writer.write_data_to_s3(prefix + "addressBookIDKey.json", json.dumps(user_to_id))

    return {"statusCode": 200}
```

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
