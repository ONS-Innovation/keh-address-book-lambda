import json
import pytest
from s3writer import S3Writer

@pytest.fixture
def logger_spy():
    class LoggerSpy:
        def __init__(self):
            self.infos = []
            self.errors = []
            self.warnings = []

        def log_info(self, message):
            self.infos.append(message)

        def log_error(self, message):
            self.errors.append(message)

        def log_warning(self, message):
            self.warnings.append(message)

    return LoggerSpy()

@pytest.fixture
def s3_client():
    class FakeS3Client:
        def __init__(self, **kwargs):
            pass
        
        def put_object(self, **kwargs):
            raise Exception
        
    return FakeS3Client()


def test_writes_to_s3_success(logger_spy):
    captured = {"calls": []}

    class FakeS3Client:
        def put_object(self, **kwargs):
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
    class FailingS3Client:
        def put_object(self, **kwargs):
            raise RuntimeError("boom")

    writer = S3Writer(logger=logger_spy, s3_client=FailingS3Client(), bucket_name="my-bucket")

    writer.write_data_to_s3("test.json", {"a": 1})

    assert any("Unable to upload updated username and email data to S3" in m for m in logger_spy.errors)
    assert not any("Successfully uploaded" in m for m in logger_spy.infos)


def test_write_data_when_none(logger_spy):
    class GuardClient:
        def put_object(self, **kwargs):
            raise AssertionError("put_object should not be called when args are None")

    writer = S3Writer(logger=logger_spy, s3_client=GuardClient(), bucket_name="my-bucket")

    writer.write_data_to_s3(None, {"x": 1})
    writer.write_data_to_s3("k.json", None)

    assert len(logger_spy.warnings) >= 2