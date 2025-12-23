# Overview

This Lambda queries the GitHub GraphQL API for all members of the configured organisation, collects their verified org email addresses and account IDs, and writes three S3 JSON lookup files used by Digital Landscape.

Outputs (under `AddressBook/` in S3):
- `addressBookUsernameKey.json`: username → list of verified org emails
- `addressBookEmailKey.json`: email → username
- `addressBookIDKey.json`: username → GitHub account ID

See [The Process](the_process.md).

## Purpose

Provide reliable lookups between GitHub usernames, verified organisation email addresses, and GitHub account IDs so Digital Landscape can identify owners quickly and consistently.

## File Description

- `src/lambda_function.py`: Orchestrates the run and writes outputs to S3.
- `src/github_services.py`: Interfaces with GitHub GraphQL via `github-api-toolkit`.
- `src/s3writer.py`: Handles writing JSON files to S3.
- `src/logger.py`: Structured logging for observability.

## Outputs

S3 key prefix: `AddressBook/`

Example shapes:

`AddressBook/addressBookUsernameKey.json`
```json
{
	"alice": ["alice@org.com", "alice2@org.com"],
	"bob": ["bob@org.com"]
}
```

`AddressBook/addressBookEmailKey.json`
```json
{
	"alice@org.com": "alice",
	"bob@org.com": "bob"
}
```

`AddressBook/addressBookIDKey.json`
```json
{
	"alice": 101,
	"bob": 202
}
```

## Limitations & Assumptions

- Only verified organisation emails are included in mappings.
- Subject to GitHub API rate limits; the implementation handles normal org sizes.

## Next Steps

- Read the detailed flow: [The Process](the_process.md)
- Configure environment and IAM: [Configuration](configuration.md)