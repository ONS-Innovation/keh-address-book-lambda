import json
import os
import builtins

import pytest
from unittest.mock import Mock, patch, call, ANY


@pytest.fixture
def set_env(monkeypatch):
    monkeypatch.setenv("GITHUB_ORG", "test-org")
    monkeypatch.setenv("AWS_SECRET_NAME", "test-secret")
    monkeypatch.setenv("GITHUB_APP_CLIENT_ID", "12345")


def test_lambda_happy_path(set_env):
    # Mock boto3 secretsmanager client
    with patch("lambda_function.boto3.client", return_value=Mock()) as _:
        # Mock GitHubServices to return bidirectional dicts
        with patch("lambda_function.GitHubServices") as fake_services_cls, \
             patch("lambda_function.S3Writer") as fake_s3writer_cls:

            fake_services = fake_services_cls.return_value
            fake_services.get_all_user_details.return_value = (
                {"alice": "alice@ons.gov.uk", "bob": "bob@ons.gov.uk"},
                {"alice@ons.gov.uk": "alice", "bob@ons.gov.uk": "bob"},
            )

            fake_s3writer = fake_s3writer_cls.return_value

            # Import and run handler
            from lambda_function import lambda_handler

            result = lambda_handler(event={}, context=None)

            # Handler returns structured success response
            assert isinstance(result, dict)
            assert result.get('statusCode') == 200
            body = json.loads(result.get('body', '{}'))
            assert body.get('message')
            fake_services.get_all_user_details.assert_called_once()

            # Verify S3 uploads with JSON content
            assert fake_s3writer.write_data_to_s3.call_count == 2
            expected_calls = [
                call("addressBookUsernameKey.json", ANY),
                call("addressBookEmailKey.json", ANY),
            ]
            fake_s3writer.write_data_to_s3.assert_has_calls(expected_calls, any_order=True)

            # Validate JSON payload shapes
            args_list = [c.args for c in fake_s3writer.write_data_to_s3.call_args_list]
            for _, payload in args_list:
                parsed = json.loads(payload)
                assert isinstance(parsed, dict)


def test_lambda_missing_env_var(monkeypatch):
    # Ensure a required env var is missing
    for key in ("GITHUB_ORG", "AWS_SECRET_NAME", "GITHUB_APP_CLIENT_ID"):
        if key in os.environ:
            monkeypatch.delenv(key, raising=False)

    # Mock dependencies minimally to avoid real calls
    with patch("lambda_function.boto3.client"), patch("lambda_function.GitHubServices"), patch("lambda_function.S3Writer"):
        from lambda_function import lambda_handler

        # Expect a 400 response due to missing env configuration
        result = lambda_handler(event={}, context=None)
        assert isinstance(result, dict)
        assert result.get('statusCode') == 500
        body = json.loads(result.get('body', '{}'))
        assert body.get('message') == 'Missing required environment variables'


def test_lambda_serializes_and_uploads(set_env):
    # Mock boto3 secretsmanager client
    with patch("lambda_function.boto3.client", return_value=Mock()):
        # Provide simple deterministic mappings
        with patch("lambda_function.GitHubServices") as fake_services_cls, \
             patch("lambda_function.S3Writer") as fake_s3writer_cls:

            fake_services = fake_services_cls.return_value
            user_to_email = {"user": "user@ons.gov.uk"}
            email_to_user = {"user@ons.gov.uk": "user"}
            fake_services.get_all_user_details.return_value = (user_to_email, email_to_user)

            fake_s3writer = fake_s3writer_cls.return_value

            from lambda_function import lambda_handler

            result = lambda_handler(event={}, context=None)
            assert result.get('statusCode') == 200

            # Extract payloads and validate exact JSON
            args1 = fake_s3writer.write_data_to_s3.call_args_list[0][0]
            args2 = fake_s3writer.write_data_to_s3.call_args_list[1][0]

            assert args1[0] in {"addressBookUsernameKey.json", "addressBookEmailKey.json"}
            assert args2[0] in {"addressBookUsernameKey.json", "addressBookEmailKey.json"}

            payloads = {args1[0]: args1[1], args2[0]: args2[1]}
            assert json.loads(payloads["addressBookUsernameKey.json"]) == user_to_email
            assert json.loads(payloads["addressBookEmailKey.json"]) == email_to_user
