# FAQ - tes

Below are common questions and quick fixes when using the Address Book Lambda.

## Outputs and Data

### What does the Lambda produce?

- Three JSON files in S3 under the `AddressBook/` prefix:
  - `addressBookUsernameKey.json`: username → list of verified org emails
  - `addressBookEmailKey.json`: email → username
  - `addressBookIDKey.json`: username → GitHub account ID

### How often does the Lambda run?

- The schedule is controlled by EventBridge via Terraform variables in `terraform/service/env/*/*.tfvars`.

### Where are the files written?

- To the bucket specified by `S3_BUCKET_NAME`, under the `AddressBook/` prefix.

### Why are some users missing email addresses?

- Only verified organisation emails are included by design. Users without a verified org email won’t appear in the email-based mappings.

## Documentation (MkDocs)

### `make mkdocs-serve` fails or pages 404.

- The target is `docs-serve`, not `mkdocs-serve`. Also ensure `mkdocs.yml` nav matches files in `docs/`.

For a deeper dive, see:

- [Overview](technical_documentation/overview.md)
- [The Process](technical_documentation/the_process.md)
- [Configuration](technical_documentation/configuration.md)
