# S3 Writer (API)

Writes JSON data to the configured S3 bucket and logs success/failure.

## Overview

- Constructor requires: `logger`, `s3_client` (boto3), and `bucket_name`.
- Validates `bucket_name` is set; otherwise raises `ValueError`.
- Method `write_data_to_s3(file_to_update, data)` uploads JSON to `s3://<bucket>/<file_to_update>`.

## Quick Start

```python
import boto3, json
from s3writer import S3Writer
from logger import wrapped_logging

logger = wrapped_logging(False)
s3 = boto3.client("s3")

writer = S3Writer(logger, s3, bucket_name="<bucket>")

payload = {"alice": ["alice@org.com"], "bob": ["bob@org.com"]}
writer.write_data_to_s3("AddressBook/addressBookUsernameKey.json", payload)
```

## Errors

- Raises `Exception` if `file_to_update` or `data` is `None`.
- Logs errors and re-raises on S3 failures (e.g., access denied).

## Reference

::: s3writer
