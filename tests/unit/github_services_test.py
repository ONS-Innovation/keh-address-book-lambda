import pytest
import github_services
from fixtures import logger_spy, secret_manager_valid, secret_manager_empty


def test_github_services_valid(monkeypatch, logger_spy, secret_manager_valid):
    """Ensures valid GitHubServices setup succeeds and logs nothing."""

    def fake_get_token_as_installation(org, pem, app_client_id):
        """Return fake token."""

        assert org == "test-org"
        assert pem == "FAKE_PEM_CONTENT"
        assert app_client_id == "12345"
        return ("token123", "inst1")
    
    
    class FakeResponse:
        def json(self):
            """Fake response."""
            return {
                "data": {
                    "organization": {
                        "membersWithRole": {
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                            "nodes": []
                        }
                    }
                }
            }

    class FakeQL:
        def make_ql_request(self, query, params):
            """Recreate GraphQL request; returns FakeResponse."""
            return FakeResponse()


    monkeypatch.setattr(github_services.github_api_toolkit, "get_token_as_installation", fake_get_token_as_installation)
    monkeypatch.setattr(github_services.github_api_toolkit, "github_graphql_interface", lambda token: FakeQL(),)

    services = github_services.GitHubServices(
        org="test-org",
        logger=logger_spy,
        secret_manager=secret_manager_valid,
        secret_name="test-secret",
        app_client_id="12345"
    )

    assert isinstance(services.ql, FakeQL)
    assert logger_spy.all_calls == []


def test_missing_secret(logger_spy, secret_manager_empty):
    """Raises when secret is missing and logs an error."""

    with pytest.raises(Exception) as exc:
        _ = github_services.GitHubServices(
            org="test-org",
            logger=logger_spy,
            secret_manager=secret_manager_empty,
            secret_name="test-secret",
            app_client_id="12345",
        )

    msg = str(exc.value)
    assert "Secret test-secret not found in AWS Secret Manager" in msg

    assert len(logger_spy.all_calls) == 1
    assert "Secret test-secret not found in AWS Secret Manager" in logger_spy.all_calls[0]


def test_bad_token(monkeypatch, logger_spy, secret_manager_valid):
    """Handles invalid token retrieval by raising and logging."""

    def fake_bad_token(org, pem, app_client_id):
        """Return failure to recreate a bad token."""
        return "failure"

    monkeypatch.setattr(
        github_services.github_api_toolkit,
        "get_token_as_installation",
        fake_bad_token,
    )

    with pytest.raises(Exception) as exc:
        _ = github_services.GitHubServices(
            org="test-org",
            logger=logger_spy,
            secret_manager=secret_manager_valid,
            secret_name="test-secret",
            app_client_id="12345",
        )

    assert str(exc.value) == "failure"
    assert any("Failed to retrieve GitHub App installation token" in m for m in logger_spy.all_calls)


def test_get_all_user_details(monkeypatch, logger_spy, secret_manager_valid):
    """Paginates members correctly."""

    monkeypatch.setattr(
        github_services.github_api_toolkit,
        "get_token_as_installation",
        lambda org, pem, app_client_id: ("token123", "inst1"),
    )

    calls = {"count": 0, "params": []}

    class FakeResponse1:
        """First page payload with pagination cursor."""
        def json(self):
            return {
                "data": {
                    "organization": {
                        "membersWithRole": {
                            "pageInfo": {"hasNextPage": True, "endCursor": "CUR1"},
                            "nodes": [
                                {"login": "alice", "databaseId": 101, "organizationVerifiedDomainEmails": ["a@org.com", "a2@org.com"]}
                            ],
                        }
                    }
                }
            }

    class FakeResponse2:
        """Second page payload; end of pagination."""
        def json(self):
            return {
                "data": {
                    "organization": {
                        "membersWithRole": {
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                            "nodes": [
                                {"login": "bob", "databaseId": 202, "organizationVerifiedDomainEmails": ["b@org.com"]}
                            ],
                        }
                    }
                }
            }

    class FakeQL:
        def make_ql_request(self, query, params):
            """Recreate paginated GraphQL; track calls and params."""
            calls["count"] += 1
            calls["params"].append(params)
            return FakeResponse1() if calls["count"] == 1 else FakeResponse2()

    monkeypatch.setattr(
        github_services.github_api_toolkit,
        "github_graphql_interface",
        lambda token: FakeQL(),
    )

    services = github_services.GitHubServices(
        org="test-org",
        logger=logger_spy,
        secret_manager=secret_manager_valid,
        secret_name="test-secret",
        app_client_id="12345",
    )

    user_to_email, email_to_user, user_to_id = services.get_all_user_details()

    assert user_to_email == {
        "alice": ["a@org.com", "a2@org.com"],
        "bob": ["b@org.com"],
    }
    assert email_to_user["a@org.com"] == "alice"
    assert email_to_user["a2@org.com"] == "alice"
    assert email_to_user["b@org.com"] == "bob"

    assert user_to_id == {"alice": 101, "bob": 202}

    assert logger_spy.all_calls == []


def test_missing_email(monkeypatch, logger_spy, secret_manager_valid):
    """Skips members with no verified domain emails."""

    monkeypatch.setattr(
        github_services.github_api_toolkit,
        "get_token_as_installation",
        lambda org, pem, app_client_id: ("token123", "inst1"),
    )

    class FakeResponse:
        def json(self):
            """Fake response with empty email list."""
            return {
                "data": {
                    "organization": {
                        "membersWithRole": {
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                            "nodes": [
                                {"login": "alice", "organizationVerifiedDomainEmails": []}
                            ],
                        }
                    }
                }
            }

    class FakeQL:
        def make_ql_request(self, query, params):
            """Recreate GraphQL request; returns FakeResponse."""
            return FakeResponse()

    monkeypatch.setattr(
        github_services.github_api_toolkit,
        "github_graphql_interface",
        lambda token: FakeQL(),
    )

    services = github_services.GitHubServices(
        org="test-org",
        logger=logger_spy,
        secret_manager=secret_manager_valid,
        secret_name="test-secret",
        app_client_id="12345",
    )

    user_to_email, email_to_user, user_to_id = services.get_all_user_details()
    
    assert user_to_email == {}
    assert email_to_user == {}
    assert user_to_id == {}

    assert any("Skipping member 'alice' with no verified domain emails" in m for m in logger_spy.all_calls)


def test_missing_username(monkeypatch, logger_spy, secret_manager_valid):
    """Skips members with empty usernames."""

    monkeypatch.setattr(
        github_services.github_api_toolkit,
        "get_token_as_installation",
        lambda org, pem, app_client_id: ("token123", "inst1"),
    )

    class FakeResponse:
        """Fake response payload lacking username."""
        def json(self):
            return {
                "data": {
                    "organization": {
                        "membersWithRole": {
                            "pageInfo": {"hasNextPage": False, "endCursor": None},
                            "nodes": [
                                {"login": "", "organizationVerifiedDomainEmails": ["a@123.com"]}
                            ],
                        }
                    }
                }
            }

    class FakeQL:
        def make_ql_request(self, query, params):
            """Recreate GraphQL request; returns FakeResponse."""
            return FakeResponse()

    monkeypatch.setattr(
        github_services.github_api_toolkit,
        "github_graphql_interface",
        lambda token: FakeQL(),
    )

    services = github_services.GitHubServices(
        org="test-org",
        logger=logger_spy,
        secret_manager=secret_manager_valid,
        secret_name="test-secret",
        app_client_id="12345",
    )

    user_to_email, email_to_user, user_to_id = services.get_all_user_details()
    
    assert user_to_email == {}
    assert email_to_user == {}
    assert user_to_id == {}

    assert any("Skipping member with empty username" in m for m in logger_spy.all_calls)
    

def test_get_all_user_details_no_org(monkeypatch, logger_spy, secret_manager_valid):
    """Handles missing organisation in GraphQL response."""
    
    monkeypatch.setattr(
        github_services.github_api_toolkit,
        "get_token_as_installation",
        lambda org, pem, app_client_id: ("token123", "inst1"),
    )

    class FakeResponse:
        def json(self):
            """Fake response with null organisation."""
            return {"data": {"organization": None}}

    class FakeQL:
        def make_ql_request(self, query, params):
            """Recreate GraphQL request; returns FakeResponse."""
            return FakeResponse()

    monkeypatch.setattr(
        github_services.github_api_toolkit,
        "github_graphql_interface",
        lambda token: FakeQL(),
    )

    services = github_services.GitHubServices(
        org="test-org",
        logger=logger_spy,
        secret_manager=secret_manager_valid,
        secret_name="secret",
        app_client_id="12345",
    )

    result = services.get_all_user_details()
    assert result[0] == "NotFound"
    assert "Organisation 'test-org not found or inaccessible'" in result[1]
    assert any("Organisation 'test-org not found or inaccessible'" in m for m in logger_spy.all_calls)