# Logging

Logging is implemented via a wrapper around Python’s `logging` module in `src/logger.py`.

## API

Class: `wrapped_logging(debug: bool)`

- `log_info(message: str)`: log at INFO.
- `log_error(message: str)`: log at ERROR.
- `log_warning(message: str)`: log at WARNING.

Behaviour:

- Default level is `INFO`.
- When `debug=True`, `logging.basicConfig(filename="debug.log", filemode="w")` writes a debug file locally (useful during development).

## Usage

```python
from logger import wrapped_logging

logger = wrapped_logging(False)  # use True to write debug.log locally

logger.log_info("Start address book run")
logger.log_warning("No verified emails for user: alice")
logger.log_error("Failed to write to S3: access denied")
```

In the Lambda handler (`src/lambda_function.py`), the logger is created once and passed to helpers:

```python
logger = wrapped_logging(False)
```

## CloudWatch Logs

- Lambda automatically forwards stdout/stderr from Python logging to CloudWatch Logs for the function.
- Use logs to track: start/end of runs, GitHub API calls, S3 writes, and errors.

## Best Practices

- Prefer INFO for milestones, WARNING for recoverable anomalies, ERROR for failures.
- Add context to messages (org, bucket, key) to aid debugging.
- Avoid writing secrets or sensitive personal data to logs.
- For local dev, consider `debug=True` to capture a `debug.log`, but disable before committing.
