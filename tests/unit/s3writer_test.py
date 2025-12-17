import json
import pytest
from s3writer import S3Writer
from fixtures import logger_spy, s3_client


def test_writes_to_s3_success(logger_spy):
    """Uploads JSON to S3 successfully and logs an info message."""
    captured = {"calls": []}

    class FakeS3Client:
        def put_object(self, **kwargs):
            """Store call arguments and simulate a 200 response."""
            captured["calls"].append(kwargs)
            return {"ResponseMetadata": {"HTTPStatusCode": 200}}

    writer = S3Writer(logger=logger_spy, s3_client=FakeS3Client(), bucket_name="my-bucket")

    payload = {"a": 1}
    key = "test.json"
    writer.write_data_to_s3(key, payload)

    assert len(captured["calls"]) == 1
    call = captured["calls"][0]
    assert call["Bucket"] == "my-bucket"
    assert call["Key"] == key
    assert call["ContentType"] == "application/json"

    body = call["Body"]
    assert isinstance(body, (bytes, bytearray))
    decoded = body.decode("utf-8")
    assert json.loads(decoded) == payload

    assert any("Successfully uploaded updated username and email data to S3" in m for m in logger_spy.infos)
    assert logger_spy.errors == []


def test_writes_to_s3_error_logs(logger_spy):
    """Logs an error and raises when the S3 upload fails."""
    class FailingS3Client:
        def put_object(self, **kwargs):
            raise RuntimeError("boom")

    writer = S3Writer(logger=logger_spy, s3_client=FailingS3Client(), bucket_name="my-bucket")

    with pytest.raises(RuntimeError):
        writer.write_data_to_s3("test.json", {"a": 1})

    assert any("Unable to upload updated username and email data to S3" in m for m in logger_spy.errors)
    assert not any("Successfully uploaded" in m for m in logger_spy.infos)


def test_write_data_when_none(logger_spy):
    """Validates guard behaviour when filename or data is empty."""
    class GuardClient:
        """Protect against unintended `put_object` calls in tests."""
        def put_object(self, **kwargs):
            """Should never be called when arguments are None."""
            raise AssertionError("put_object should not be called when args are None")

    writer = S3Writer(logger=logger_spy, s3_client=GuardClient(), bucket_name="my-bucket")

    with pytest.raises(Exception):
        writer.write_data_to_s3(None, {"x": 1})
    with pytest.raises(Exception):
        writer.write_data_to_s3("k.json", None)

    assert any("filename or data is empty" in m for m in logger_spy.errors)