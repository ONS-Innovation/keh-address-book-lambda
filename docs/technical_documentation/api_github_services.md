# GitHub Services (API)

Encapsulates interactions with the GitHub GraphQL API using `github_api_toolkit` and a GitHub App installation token.

## Overview

- Receives the GitHub client ID and private key from the Lambda handler and uses them to retrieve a GitHub App installation token. Secret Manager access and secret parsing are handled by the handler.
- Builds a GraphQL client interface for requests.
- Provides `get_all_user_details()` which returns:
  - `user_to_email`: username → list of verified org emails
  - `email_to_user`: email → username
  - `user_to_id`: username → GitHub account ID
  - Or a tuple `("NotFound", <message>)` if the org is missing/inaccessible.

## Quick Start

```python
from github_services import GitHubServices
from logger import wrapped_logging

logger = wrapped_logging(False)

svc = GitHubServices(
 org="<org>",
 logger=logger,
 github_client_id="<github_client_id>",
 github_private_key="<github_private_key_pem>",
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
