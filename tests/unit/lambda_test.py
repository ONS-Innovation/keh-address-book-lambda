import json
import pytest
from lambda_function import lambda_handler
from fixtures import logger_spy, set_env


def _patch_aws_clients(monkeypatch, secret_overrides=None):
    alert_calls = []

    class FakeSecretsManager:
        def get_secret_value(self, SecretId):
            secrets = {
                "github-client-id": '{"ClientID": "12345"}',
                "github-private-key": "FAKE_PEM_CONTENT",
                "alert-secret": json.dumps(
                    {
                        "azure_tenant_id": "tenant",
                        "azure_client_id": "client",
                        "azure_client_secret": "secret",
                        "azure_webhook_url": "https://example.test/webhook",
                        "channel_id": "channel",
                    }
                ),
            }
            secrets.update(secret_overrides or {})
            return {"SecretString": secrets[SecretId]}

    class FakeTeamsAlertClient:
        def __init__(self, **kwargs):
            pass

        def post_to_webhook(self, **kwargs):
            alert_calls.append(kwargs)

    monkeypatch.setattr(
        "lambda_function.boto3.client",
        lambda name: FakeSecretsManager() if name == "secretsmanager" else object(),
    )
    monkeypatch.setattr("lambda_function.TeamsAlertClient", FakeTeamsAlertClient)
    return alert_calls


def test_lambda_aws_client_failure(set_env, monkeypatch, logger_spy):
    """Raises and logs when an AWS client cannot be created."""
    monkeypatch.setattr(
        "lambda_function.boto3.client",
        lambda name: (_ for _ in ()).throw(RuntimeError("AWS unavailable")),
    )
    monkeypatch.setattr("lambda_function.wrapped_logging", lambda _: logger_spy)

    with pytest.raises(Exception, match="Unable to retrieve Secret Manager"):
        lambda_handler(event={}, context=None)

    assert len(logger_spy.errors) == 1


@pytest.mark.parametrize(
    ("secret_name", "secret_value"),
    (
        ("github-client-id", '{"ClientID": ""}'),
        ("github-private-key", ""),
    ),
)
def test_lambda_missing_github_credential(
    set_env, monkeypatch, secret_name, secret_value
):
    """Raises when either required GitHub credential is empty."""
    _patch_aws_clients(monkeypatch, {secret_name: secret_value})

    with pytest.raises(
        Exception, match="GitHub Client ID or Private Key not found in Secrets Manager"
    ):
        lambda_handler(event={}, context=None)


def test_lambda_missing_alert_secret_key(set_env, monkeypatch):
    """Raises when the alert secret omits a required value."""
    _patch_aws_clients(
        monkeypatch,
        {
            "alert-secret": json.dumps(
                {
                    "azure_client_id": "client",
                    "azure_client_secret": "secret",
                    "azure_webhook_url": "https://example.test/webhook",
                    "channel_id": "channel",
                }
            )
        },
    )
    monkeypatch.setattr("lambda_function.GitHubServices", lambda *args: object())

    with pytest.raises(
        Exception, match="Missing required alert secret key: azure_tenant_id"
    ):
        lambda_handler(event={}, context=None)


def test_lambda_handles_github_fetch_failure(set_env, monkeypatch):
    """Notifies the alert channel and raises when GitHub data retrieval fails."""
    alert_calls = _patch_aws_clients(monkeypatch)

    class FailingServices:
        def get_all_user_details(self):
            raise RuntimeError("GitHub boom")

    monkeypatch.setattr(
        "lambda_function.GitHubServices", lambda *args: FailingServices()
    )

    with pytest.raises(
        Exception, match="Failed to fetch data from GitHub: GitHub boom"
    ):
        lambda_handler(event={}, context=None)

    assert len(alert_calls) == 1
    assert alert_calls[0]["webhook_url"] == "https://example.test/webhook"
    assert alert_calls[0]["payload"]["channel"] == "channel"
    assert "GitHub boom" in alert_calls[0]["payload"]["message"]


def test_lambda_valid(set_env, monkeypatch):
    """Processes a valid event, writes to S3, returns 200."""
    _patch_aws_clients(monkeypatch)

    class GitHubServices:
        def __init__(self):
            self.calls = 0

        def get_all_user_details(self):
            self.calls += 1
            return (
                {"alice": "alice@ons.gov.uk", "bob": "bob@ons.gov.uk"},
                {"alice@ons.gov.uk": "alice", "bob@ons.gov.uk": "bob"},
                {"alice": 101, "bob": 202},
            )

    class S3WriterStub:
        """Capture S3 writes for verification."""

        def __init__(self):
            self.call_args_list = []

        def write_data_to_s3(self, filename, payload):
            """Record filename and payload as a captured call."""
            self.call_args_list.append(((filename, payload), {}))

    services_stub = GitHubServices()
    s3writer_stub = S3WriterStub()

    monkeypatch.setattr("lambda_function.GitHubServices", lambda *a, **k: services_stub)
    monkeypatch.setattr("lambda_function.S3Writer", lambda *a, **k: s3writer_stub)

    result = lambda_handler(event={}, context=None)

    assert isinstance(result, dict)
    assert result.get("statusCode") == 200
    body = json.loads(result.get("body", "{}"))
    assert body.get("message")
    assert services_stub.calls == 1

    assert len(s3writer_stub.call_args_list) == 3
    filenames = {args[0] for args, _ in s3writer_stub.call_args_list}
    assert filenames == {
        "AddressBook/addressBookUsernameKey.json",
        "AddressBook/addressBookEmailKey.json",
        "AddressBook/addressBookIDKey.json",
    }
    for (filename, payload), _ in s3writer_stub.call_args_list:
        parsed = json.loads(payload)
        assert isinstance(parsed, dict)


@pytest.mark.parametrize(
    "missing_variable",
    (
        "GITHUB_ORG",
        "S3_BUCKET_NAME",
        "GITHUB_CLIENT_ID_SECRET_NAME",
        "GITHUB_PRIVATE_KEY_SECRET_NAME",
        "ALERT_SECRET_NAME",
    ),
)
def test_lambda_missing_env_var(monkeypatch, missing_variable):
    """Raises when any required environment variable is missing."""
    for variable in (
        "GITHUB_ORG",
        "S3_BUCKET_NAME",
        "GITHUB_CLIENT_ID_SECRET_NAME",
        "GITHUB_PRIVATE_KEY_SECRET_NAME",
        "ALERT_SECRET_NAME",
    ):
        monkeypatch.setenv(variable, "test-value")
    monkeypatch.delenv(missing_variable)

    with pytest.raises(Exception) as excinfo:
        lambda_handler(event={}, context=None)

    assert f"{missing_variable} environment variable not set" == str(excinfo.value)


def test_lambda_handles_org_not_found(set_env, monkeypatch):
    """Returns 404 when the organisation cannot be found."""
    _patch_aws_clients(monkeypatch)

    class FakeServices:
        def __init__(self, *args, **kwargs):
            pass

        def get_all_user_details(self):
            return ("NotFound", "Organisation 'test-org not found or inaccessible'")

    monkeypatch.setattr(
        "lambda_function.GitHubServices", lambda *a, **k: FakeServices()
    )

    class FakeS3Writer:
        def __init__(self, *args, **kwargs):
            pass

        def write_data_to_s3(self, *args, **kwargs):
            pass

    monkeypatch.setattr("lambda_function.S3Writer", lambda *a, **k: FakeS3Writer())

    result = lambda_handler(event={}, context=None)
    assert result["statusCode"] == 404
    body = json.loads(result["body"])
    msg = body.get("message", "")
    assert isinstance(msg, str) and "Organisation" in msg and "not found" in msg


def test_lambda_handles_s3_write_failure(set_env, monkeypatch):
    """Returns 500 when S3 write fails and message is logged."""
    _patch_aws_clients(monkeypatch)

    class FakeServices:
        def __init__(self, *args, **kwargs):
            pass

        def get_all_user_details(self):
            return (
                {"alice": "alice@ons.gov.uk"},
                {"alice@ons.gov.uk": "alice"},
                {"alice": 101},
            )

    monkeypatch.setattr(
        "lambda_function.GitHubServices", lambda *a, **k: FakeServices()
    )

    class FailingS3Writer:
        def __init__(self, *args, **kwargs):
            pass

        def write_data_to_s3(self, *args, **kwargs):
            raise RuntimeError("S3 boom")

    monkeypatch.setattr("lambda_function.S3Writer", lambda *a, **k: FailingS3Writer())

    with pytest.raises(Exception) as excinfo:
        lambda_handler(event={}, context=None)

    assert "S3 boom" in str(excinfo.value)
