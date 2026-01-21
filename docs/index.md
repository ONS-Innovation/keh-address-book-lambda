# GitHub Repository Address Book Lambda - TEST

This site documents the Address Book Lambda that collects GitHub usernames, verified org emails, and account IDs, and writes JSON lookup files to S3 for use by Digital Landscape.

- What it does, how it works, and how to configure it
- How to run and develop locally
- FAQs and troubleshooting tips

### What the Address Book Lambda function does?

This Lambda function makes a request to GitHub to retrieve the usernames, organisation emails and account IDs for every ONS Digital GitHub user. This data is then organised into 3 dictionaries which are then put into the Digital Landscape AWS S3 bucket for later retrieval.

### How does the Address Book Lambda function work?

- Authenticate with GitHub using GitHub App credentials provided via environment variables.
- Query the organisation via the GitHub GraphQL API (using [`github-api-toolkit`](https://github.com/ONS-Innovation/github-api-package)) to retrieve GitHub usernames, verified org emails and account IDs.
- Build three dictionaries:
  - username → list of verified org emails
  - email → username
  - username → GitHub account ID
- Write the JSON outputs to the placed in the S3 bucket under the `AddressBook/` prefix.
- Log progress and errors; failures are visible in CloudWatch.

- Read more... [The Process](technical_documentation/the_process.md)

Quick links:

- Technical Overview: [Overview](technical_documentation/overview.md)
- Pipeline: [The Process](technical_documentation/the_process.md)
- Configuration: [Configuration](technical_documentation/configuration.md)
- Logging: [Logging](technical_documentation/logging.md)
- Docs Usage: [Documentation](documentation.md)
