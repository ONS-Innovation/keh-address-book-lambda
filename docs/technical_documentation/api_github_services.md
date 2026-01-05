# GitHub Services (API)

Encapsulates interactions with the GitHub GraphQL API using `github_api_toolkit` and a GitHub App installation token.

## Overview

- Retrieves a GitHub App installation token via AWS Secrets Manager (`AWS_SECRET_NAME`) and the provided `GITHUB_APP_CLIENT_ID`.
- Builds a GraphQL client interface for requests.
- Provides `get_all_user_details()` which returns:
  - `user_to_email`: username → list of verified org emails
  - `email_to_user`: email → username
  - `user_to_id`: username → GitHub account ID
  - Or a tuple `("NotFound", <message>)` if the org is missing/inaccessible.

## Quick Start

```python
import boto3
from github_services import GitHubServices
from logger import wrapped_logging

logger = wrapped_logging(False)
sm = boto3.client("secretsmanager")

svc = GitHubServices(
	org="<org>",
	logger=logger,
	secret_manager=sm,
	secret_name="<aws_secret_name>",
	app_client_id="<github_app_client_id>",
)

result = svc.get_all_user_details()
if isinstance(result, tuple) and result[0] == "NotFound":
	logger.log_error(f"Org issue: {result[1]}")
else:
	user_to_email, email_to_user, user_to_id = result
```

## Notes

- Skips members with no verified org emails and logs a warning.
- Paginates through org members in batches of 100.
- Errors retrieving tokens or invalid secrets raise exceptions.

## Reference

::: github_services
