import json
import os
import builtins
import pytest
from lambda_function import lambda_handler


@pytest.fixture
def set_env(monkeypatch):
    monkeypatch.setenv("GITHUB_ORG", "test-org")
    monkeypatch.setenv("AWS_SECRET_NAME", "test-secret")
    monkeypatch.setenv("GITHUB_APP_CLIENT_ID", "12345")


def test_lambda_valid(monkeypatch):
    class GitHubServices:
        def __init__(self):
            self.calls = 0

        def get_all_user_details(self):
            self.calls += 1
            return (
                {"alice": "alice@ons.gov.uk", "bob": "bob@ons.gov.uk"},
                {"alice@ons.gov.uk": "alice", "bob@ons.gov.uk": "bob"},
            )

    class S3WriterStub:
        def __init__(self):
            self.call_args_list = []

        def write_data_to_s3(self, filename, payload):
            self.call_args_list.append(((filename, payload), {}))

    services_stub = GitHubServices()
    s3writer_stub = S3WriterStub()

    monkeypatch.setattr("lambda_function.GitHubServices", lambda *a, **k: services_stub)
    monkeypatch.setattr("lambda_function.S3Writer", lambda *a, **k: s3writer_stub)

    result = lambda_handler(event={}, context=None)

    assert isinstance(result, dict)
    assert result.get('statusCode') == 200
    body = json.loads(result.get('body', '{}'))
    assert body.get('message')
    assert services_stub.calls == 1

    assert len(s3writer_stub.call_args_list) == 2
    filenames = {args[0] for args, _ in s3writer_stub.call_args_list}
    assert filenames == {"addressBookUsernameKey.json", "addressBookEmailKey.json"}
    for (filename, payload), _ in s3writer_stub.call_args_list:
        parsed = json.loads(payload)
        assert isinstance(parsed, dict)


def test_lambda_missing_env_var(monkeypatch):
    for key in ("GITHUB_ORG", "AWS_SECRET_NAME", "GITHUB_APP_CLIENT_ID"):
        if key in os.environ:
            monkeypatch.delenv(key, raising=False)

    monkeypatch.setattr("lambda_function.boto3.client", lambda name: object())
    monkeypatch.setattr("lambda_function.GitHubServices", lambda *a, **k: object())
    monkeypatch.setattr("lambda_function.S3Writer", lambda *a, **k: object())

    from lambda_function import lambda_handler

    result = lambda_handler(event={}, context=None)
    assert isinstance(result, dict)
    assert result.get('statusCode') == 500
    body = json.loads(result.get('body', '{}'))
    assert body.get('message') == 'Missing required environment variables'


def test_lambda_handles_org_not_found(set_env, monkeypatch):
    monkeypatch.setattr("lambda_function.boto3.client", lambda name: object())

    class FakeServices:
        def __init__(self, *args, **kwargs): pass
        def get_all_user_details(self):
            return ("NotFound", "Organisation 'test-org not found or inaccessible'")

    monkeypatch.setattr("lambda_function.GitHubServices", lambda *a, **k: FakeServices())

    class FakeS3Writer:
        def __init__(self, *args, **kwargs): pass
        def write_data_to_s3(self, *args, **kwargs): pass

    monkeypatch.setattr("lambda_function.S3Writer", lambda *a, **k: FakeS3Writer())

    result = lambda_handler(event={}, context=None)
    assert result["statusCode"] == 404
    body = json.loads(result["body"])
    msg = body.get("message", "")
    assert isinstance(msg, str) and "Organisation" in msg and "not found" in msg


def test_lambda_handles_s3_write_failure(set_env, monkeypatch):
    monkeypatch.setattr("lambda_function.boto3.client", lambda name: object())

    class FakeServices:
        def __init__(self, *args, **kwargs): pass
        def get_all_user_details(self):
            return ({"alice": "alice@ons.gov.uk"}, {"alice@ons.gov.uk": "alice"})

    monkeypatch.setattr("lambda_function.GitHubServices", lambda *a, **k: FakeServices())

    class FailingS3Writer:
        def __init__(self, *args, **kwargs): pass
        def write_data_to_s3(self, *args, **kwargs):
            raise RuntimeError("S3 boom")

    monkeypatch.setattr("lambda_function.S3Writer", lambda *a, **k: FailingS3Writer())

    result = lambda_handler(event={}, context=None)
    assert result["statusCode"] == 500
    body = json.loads(result["body"])
    assert body.get("message")