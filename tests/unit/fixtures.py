import pytest


@pytest.fixture
def logger_spy():
    class LoggerSpy:
        def __init__(self):
            self.infos = []
            self.errors = []
            self.warnings = []
            self.all_calls = []

        def log_info(self, message):
            self.infos.append(message)
            self.all_calls.append(message)

        def log_error(self, message):
            self.errors.append(message)
            self.all_calls.append(message)

        def log_warning(self, message):
            self.warnings.append(message)
            self.all_calls.append(message)

    return LoggerSpy()


@pytest.fixture
def s3_client():
    class FakeS3Client:
        def __init__(self, **kwargs):
            pass

        def put_object(self, **kwargs):
            raise Exception

    return FakeS3Client()


@pytest.fixture
def secret_manager_valid():
    class SecretManagerValid:
        def get_secret_value(self, SecretId):
            return {"SecretString": "FAKE_PEM_CONTENT"}

    return SecretManagerValid()


@pytest.fixture
def secret_manager_empty():
    class SecretManagerEmpty:
        def get_secret_value(self, SecretId):
            return {"SecretString": ""}

    return SecretManagerEmpty()


@pytest.fixture
def set_env(monkeypatch):
    monkeypatch.setenv("GITHUB_ORG", "test-org")
    monkeypatch.setenv("S3_BUCKET_NAME", "test-bucket")
    monkeypatch.setenv("GITHUB_CLIENT_ID_SECRET_NAME", "github-client-id")
    monkeypatch.setenv("GITHUB_PRIVATE_KEY_SECRET_NAME", "github-private-key")
    monkeypatch.setenv("ALERT_SECRET_NAME", "alert-secret")
