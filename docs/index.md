# GitHub Repository Address Book Lambda

This site documents the Address Book Lambda that collects GitHub usernames, verified org emails, and account IDs, and writes JSON lookup files to S3 for use by Digital Landscape.

- What it does, how it works, and how to configure it
- How to run and develop locally
- FAQs and troubleshooting tips

### What the Address Book Lambda function does?

This Lambda function makes a request to GitHub to retrieve the usernames, organisation emails and account IDs for every ONS Digital GitHub user. This data is then organised into 3 dictionaries which are then put into the Digital Landscape AWS S3 bucket for later retrieval.

### How does the Address Book Lambda function work?

- Authenticate with GitHub using GitHub App credentials provided via environment variables.
- Query the organisation via the GitHub GraphQL API (using `github-api-toolkit`) to retrieve GitHub usernames, verified org emails and account IDs.
- Build three dictionaries:
  - username → list of verified org emails
  - email → username
  - username → GitHub account ID
- Write the JSON outputs to the placed in the S3 bucket under the `AddressBook/` prefix.
- Log progress and errors; failures are visible in CloudWatch.

- Read more... [The Process](technical_documentation/the_process.md)

### How to Configure the Address Book Lambda function?

Follow these steps to configure the Lambda for your environment:

1. Required configuration values
   - `AWS_REGION`: e.g., `eu-west-2`.
   - `AWS_SECRET_NAME`: Secrets Manager name holding sensitive values (if used).
   - `S3_BUCKET_NAME`: Destination bucket for AddressBook JSON outputs.
   - `GITHUB_ORG`: GitHub organisation to scan.
   - `GITHUB_APP_ID`: Numeric GitHub App ID.
   - `GITHUB_APP_CLIENT_ID`: GitHub App OAuth client ID.
   - `GITHUB_APP_CLIENT_SECRET`: GitHub App OAuth client secret.
   - For local/dev only: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`.

2. Terraform setup (recommended for AWS deployment)
   - Copy `terraform/service/env/dev/example_tfvars.txt` to your env file (e.g., `env/dev/dev.tfvars`) and fill values.
   - Initialise and deploy:
     ```bash
     cd terraform/service
     terraform init -backend-config=env/dev/backend-dev.tfbackend -reconfigure
     terraform plan -var-file=env/dev/dev.tfvars
     terraform apply -var-file=env/dev/dev.tfvars
     ```
   - This will provision/update the Lambda, its IAM role/policies, S3 access, and the EventBridge schedule (if defined in vars).

3. Verify permissions
   - Ensure the Lambda execution role has read access to `AWS_SECRET_NAME` (if used) and write access to `S3_BUCKET_NAME/AddressBook/`.

4. Local development (optional)
   - Export the variables above and run the handler locally as described in the repository README or below.

See the full details: [Configuration](technical_documentation/configuration.md)

### Developing and Running Locally

To run the Lambda function outside of a container, we need to execute the `lambda_handler()` function.

1. Uncomment the following at the bottom of `lambda_function.py` (in `./src/` folder).

   ```python
   ...
   # if __name__ == "__main__":
   #     try:
   #         lambda_handler(event={}, context=None)
   #     except Exception as e:
   #         print(f"Error running lambda_handler locally: {e}")
   ...
   ```

   **Please Note:** If uncommenting the above in `lambda_function.py`, make sure you re-comment the code _before_ pushing back to GitHub.

2. Export the required environment variables:

   ```bash
   export AWS_ACCESS_KEY_ID=<access_key_id>
   export AWS_SECRET_ACCESS_KEY=<secret_access_key>
   export AWS_REGION=eu-west-2
   export AWS_SECRET_NAME=<secret_name>
   export S3_BUCKET_NAME=<bucket_name>
   export GITHUB_ORG=<org>
   export GITHUB_APP_CLIENT_ID=<client_id>
   export GITHUB_APP_ID=<app_id>
   export GITHUB_APP_CLIENT_SECRET=<app_client_secret>

   ```

3. Run the script.

   ```bash
   poetry run python3 src/lambda_function.py
   ```

### FAQs and troubleshooting tips

- Why do I get an S3 permissions error when writing outputs?
  - Ensure the Lambda execution role has `s3:PutObject` permission on the target bucket and the `AddressBook/` prefix.

- Why are some users missing email addresses in the outputs?
  - Only verified organisation emails are included. Users without a verified org email will not appear in `addressBookUsernameKey.json` or `addressBookEmailKey.json`.

- How do I run locally and see logs?
  - Export the required environment variables (see above) and run the handler locally.

- MkDocs won’t serve or pages 404 locally.
  - Run `make install-docs` first, then `make docs-serve`. Verify `mkdocs.yml` nav matches files under `docs/`.

- How often does the Lambda run?
  - The schedule is controlled by EventBridge via Terraform variables in `terraform/service/env/*/*.tfvars`.

- Where are the outputs written?
  - To your configured S3 bucket under the `AddressBook/` prefix as three JSON files.

For more Q&A: see the dedicated [FAQ](faq.md).

Quick links:

- Technical Overview: [Overview](technical_documentation/overview.md)
- Pipeline: [The Process](technical_documentation/the_process.md)
- Configuration: [Configuration](technical_documentation/configuration.md)
- Logging: [Logging](technical_documentation/logging.md)
- Docs Usage: [Documentation](documentation.md)

To view these docs locally:

```bash
make install-docs
mkdocs serve
```
