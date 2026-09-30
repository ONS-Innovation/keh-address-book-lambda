from typing import Tuple, Any
import github_api_toolkit


class GitHubServices:
    def __init__(
        self,
        org: str,
        logger: Any,
        github_client_id: str,
        github_private_key: str,
    ):
        """
        Initialises the GitHub Services Class

        Raises:
            Exception: if GitHub app installation token is not found

        Args:
            org - Organisation name
            logger - The Lambda functions logger
            github_client_id - GitHub Client ID
            github_private_key - GitHub Private Key
        """

        self.org = org
        self.logger = logger

        token = self.get_access_token(github_client_id, github_private_key)

        # Ensure we have a valid token tuple before proceeding
        if not isinstance(token, tuple):
            self.logger.log_error(
                f"Failed to retrieve GitHub App installation token: {token}"
            )
            raise Exception(str(token))

        access_token = token[0]

        self.ql = github_api_toolkit.github_graphql_interface(access_token)

    def get_access_token(
        self, github_client_id: str, github_private_key: str
    ) -> Tuple[str, str]:
        """Gets the access token from the AWS Secret Manager.

        Args:
            github_client_id (str): The GitHub Client ID.
            github_private_key (str): The GitHub Private Key.

        Raises:
            Exception: If the secret is not found in the Secret Manager.
            Exception: if GitHub app installation token is not found

        Returns:
            str: GitHub token.
        """
        if not github_private_key:
            error_message = "GitHub private key not found. Please check your environment variables."
            self.logger.log_error(error_message)
            raise Exception(error_message)

        token = github_api_toolkit.get_token_as_installation(
            self.org, github_private_key, github_client_id
        )

        if not isinstance(token, tuple):
            self.logger.log_error(
                f"Failed to retrieve GitHub App installation token: {token}"
            )
            raise Exception(str(token))

        return token

    def get_all_user_details(self) -> tuple[dict, dict, dict] | tuple:
        """
        Retrieve all the usernames within the GitHub organisation

        Returns:
            list(dict) - members usernames, emails and account ids
        """

        user_to_email = {}
        email_to_user = {}
        user_to_id = {}
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
                                databaseId
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
                account_id = node.get("databaseId")
                emails = node.get("organizationVerifiedDomainEmails", [])

                if not username:
                    self.logger.log_warning("Skipping member with empty username")
                    continue

                if emails == [] or not emails:
                    self.logger.log_warning(
                        f"Skipping member '{username}' with no verified domain emails"
                    )
                    continue

                user_to_email[username] = emails
                if account_id is not None:
                    user_to_id[username] = account_id
                for address in emails:
                    email_to_user[address] = username

        return user_to_email, email_to_user, user_to_id
