from typing import Tuple, Any
import github_api_toolkit


class GitHubServices:
    def __init__(
        self,
        org: str,
        logger: Any,
        secret_manager: Any,
        secret_name: str,
        app_client_id: str,
    ):
        """
        Initialises the GitHub Services Class

        Args:
            org - Organisation name
            logger - The Lambda functions logger
            secret_manager - The S3 secrets manager
            secret_name - Secret name for AWS
            app_client_id - GitHub App Client ID
        """

        self.org = org
        self.logger = logger

        token = self.get_access_token(secret_manager, secret_name, app_client_id)

        # Ensure we have a valid token tuple before proceeding
        if not isinstance(token, tuple):
            self.logger.log_error(
                f"Failed to retrieve GitHub App installation token: {token}"
            )
            raise Exception(str(token))

        access_token = token[0]

        self.ql = github_api_toolkit.github_graphql_interface(access_token)

    def get_access_token(
        self, secret_manager: Any, secret_name: str, app_client_id: str
    ) -> Tuple[str, str]:
        """Gets the access token from the AWS Secret Manager.

        Args:
            secret_manager (Any): The Boto3 Secret Manager client.
            secret_name (str): The name of the secret to get.
            app_client_id (str): The client ID of the GitHub App.

        Raises:
            Exception: If the secret is not found in the Secret Manager.

        Returns:
            str: GitHub token.
        """
        response = secret_manager.get_secret_value(SecretId=secret_name)

        pem_contents = response.get("SecretString", "")

        if not pem_contents:
            error_message = f"Secret {secret_name} not found in AWS Secret Manager. Please check your environment variables."
            self.logger.log_error(error_message)
            raise Exception(error_message)

        token = github_api_toolkit.get_token_as_installation(
            self.org, pem_contents, app_client_id
        )

        if not isinstance(token, tuple):
            self.logger.log_error(
                f"Failed to retrieve GitHub App installation token: {token}"
            )
            raise Exception(str(token))

        return token

    def get_all_user_details(self) -> tuple[dict, dict] | tuple:
        """
        Retrieve all the usernames within the GitHub organisation

        Returns:
            list(dict) - members usernames and emails
        """

        user_to_email = {}
        email_to_user = {}
        has_next_page = True
        cursor = None

        while has_next_page:
            query = """
                query ($org: String!, $cursor: String) {
                    organization(login: $org) {
                        membersWithRole(first: 100, after: $cursor) {
                            pageInfo {
                                hasNextPage
                                endCursor
                            }
                            nodes {
                                login
                                organizationVerifiedDomainEmails(login: $org)
                            }
                        }
                    }
                }
            """

            params = {"org": self.org, "cursor": cursor}

            # Use instance-aware request (passes headers/token and has fallback)
            response_json = self.ql.make_ql_request(query, params).json()

            org_data = response_json.get("data", {}).get("organization")

            if not org_data:
                org_error_message = (
                    f"Organisation '{self.org} not found or inaccessible'"
                )
                self.logger.log_error(org_error_message)
                return ("NotFound", org_error_message)

            members_conn = org_data.get("membersWithRole", {})
            page_info = members_conn.get("pageInfo", {})
            has_next_page = page_info.get("hasNextPage", False)
            cursor = page_info.get("endCursor")

            for node in members_conn.get("nodes", []):
                username = node.get("login")
                emails = node.get("organizationVerifiedDomainEmails", [])

                user_to_email[username] = emails
                for address in emails:
                    email_to_user[address] = username

        return user_to_email, email_to_user
