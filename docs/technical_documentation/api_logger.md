# Logger (API)

Thin wrapper around Python’s `logging` providing simple `info`, `warning`, and `error` methods.

## Overview

- Class: `wrapped_logging(debug: bool)`
- Methods:
  - `log_info(message: str)`
  - `log_warning(message: str)`
  - `log_error(message: str)`
- Default level is `INFO`. When `debug=True`, a local `debug.log` file is written (development only).

## Quick Start

```python
from logger import wrapped_logging

logger = wrapped_logging(False)
logger.log_info("Starting run")
logger.log_warning("No verified emails for user")
logger.log_error("Failed to write S3 object")
```

## Reference

::: logger
