# FAQ

Below are common questions and quick fixes when using the Address Book Lambda.

## Outputs and Data

- What does the Lambda produce?
  - Three JSON files in S3 under the `AddressBook/` prefix:
    - `addressBookUsernameKey.json`: username → list of verified org emails
    - `addressBookEmailKey.json`: email → username
    - `addressBookIDKey.json`: username → GitHub account ID

- Where are the files written?
  - To the bucket specified by `S3_BUCKET_NAME`, under the `AddressBook/` prefix.

- Why are some users missing email addresses?
  - Only verified organisation emails are included by design. Users without a verified org email won’t appear in the email-based mappings.

## Running and Configuration

- What environment variables are required?
  - `AWS_REGION`, `S3_BUCKET_NAME`, `GITHUB_ORG`, `GITHUB_APP_ID`, `GITHUB_APP_CLIENT_ID`, `GITHUB_APP_CLIENT_SECRET`. Optionally `AWS_SECRET_NAME`. For local/dev: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`.

- How do I run the Lambda locally?
  - Export the env vars above and run:
    ```bash
    poetry run python3 src/lambda_function.py
    ```
    You can temporarily enable the `__main__` guard in `src/lambda_function.py` for convenience (remember to disable before committing).

- What IAM permissions does the Lambda need?
  - Read access to `AWS_SECRET_NAME` (if used), and `s3:PutObject` permission for `S3_BUCKET_NAME/AddressBook/*`. CloudWatch Logs permissions are required for logging.

- Why do I get S3 access denied when writing outputs?
  - Ensure the Lambda execution role policy allows `s3:PutObject` to the target bucket and `AddressBook/` prefix. Confirm KMS permissions if the bucket is encrypted with a CMK.

- I get GitHub 403/insufficient permissions.
  - Verify the GitHub App is installed on the organisation with required read scopes and that `GITHUB_APP_ID`, `GITHUB_APP_CLIENT_ID`, and `GITHUB_APP_CLIENT_SECRET` are correct.

## Terraform and Deployment

- How do I deploy to AWS?
  - Use the Terraform in `terraform/service`. Copy `env/dev/example_tfvars.txt` to `env/dev/dev.tfvars`, fill values, then run:
    ```bash
    cd terraform/service
    terraform init -backend-config=env/dev/backend-dev.tfbackend -reconfigure
    terraform plan -var-file=env/dev/dev.tfvars
    terraform apply -var-file=env/dev/dev.tfvars
    ```

## Documentation (MkDocs)

- How do I run the docs locally?
  - Install and serve:
    ```bash
    make install-docs
    make docs-serve
    ```

- `make mkdocs-serve` fails or pages 404.
  - The target is `docs-serve`, not `mkdocs-serve`. Also ensure `mkdocs.yml` nav matches files in `docs/`.

- Can I deploy docs automatically?
  - Yes. The GitHub Pages workflow `.github/workflows/docs.yml` builds on pushes to `main` and deploys to Pages.

For a deeper dive, see:

- [Overview](technical_documentation/overview.md)
- [The Process](technical_documentation/the_process.md)
- [Configuration](technical_documentation/configuration.md)
