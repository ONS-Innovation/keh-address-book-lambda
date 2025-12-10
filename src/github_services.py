import requests
import time
import jwt
from typing import Tuple, Any


class GitHubServices:
    def __init__(self, org: str, logger: Any, secret_manager: Any, secret_name: str, app_client_id: str):
        """
        Initialises the GitHubS Services Class
        
        Args:
            org - Organisation name
            logger - The Lambda functions logger
        """
        
        self.org = org
        self.logger = logger
        
        token = self.get_access_token(secret_manager, secret_name, app_client_id)

        self.api_url = "https://api.github.com/graphql"

        access_token = token[0] if isinstance(token, tuple) else token
        self.headers = {"Authorization": "token " + access_token}

        
    def get_access_token(self, secret_manager: Any, secret_name: str, app_client_id: str) -> Tuple[str, str]:
        """Gets the access token from the AWS Secret Manager.

        Args:
            secret_manager (Any): The Boto3 Secret Manager client.
            secret_name (str): The name of the secret to get.
            app_client_id (str): The client ID of the GitHub App.

        Raises:
            Exception: If the secret is not found in the Secret Manager.

        Returns:
            str: The access token.
        """
        response = secret_manager.get_secret_value(SecretId=secret_name)

        pem_contents = response.get("SecretString", "")

        if not pem_contents:
            error_message = (
                f"Secret {secret_name} not found in AWS Secret Manager. Please check your environment variables."
            )
            self.logger.log_error(error_message)
            raise Exception(error_message)

        token = self.get_token_as_installation(pem_contents, app_client_id)

        if not isinstance(token, tuple):
            self.logger.log_error(f"Failed to retrieve GitHub App installation token: {token}")
            raise Exception(str(token))

        return token
    

    def get_token_as_installation(self, pem_contents: str, app_client_id: str) -> tuple | Exception:
        """Get an access token for a GitHub App installed in an organization.

        Generates an encoded JSON Web Token (JWT) using the GitHub app client ID and the private key (pem_contents).
        The JWT is used to get the installation ID of the GitHub App in the organization.
        The installation ID is then used to get an access token for the GitHub App.
        The access token is returned along with the expiration time.

        Args:
            pem_contents (str): The contents of the private key file for the GitHub App.
            app_client_id (str): The GitHub App Client ID.

        Returns:
            A tuple containing the access token and the expiration time.
            If an error occurs, an Exception object is returned to be handled by the importing program.
        """

        # Generate JSON Web Token
        issue_time = time.time()
        expiration_time = issue_time + 600

        try:
            signing_key = jwt.jwk_from_pem(pem_contents.encode())
        except jwt.exceptions.UnsupportedKeyTypeError as err:
            return(err)

        payload = {
            # Issued at time
            "iat": int(issue_time),
            # Expiration time
            "exp": int(expiration_time),
            # Github App CLient ID
            "iss": app_client_id
        }

        jwt_instance = jwt.JWT()
        encoded_jwt = jwt_instance.encode(payload, signing_key, alg="RS256")

        # Get Installation ID
        header = {"Authorization": f"Bearer {encoded_jwt}"}
        
        try:
            response = requests.get(url=f"https://api.github.com/orgs/{self.org}/installation", headers=header)

            response.raise_for_status()

            installation_json = response.json()
            installation_id = installation_json["id"]

            # Get Access Token
            response = requests.post(url=f"https://api.github.com/app/installations/{installation_id}/access_tokens", headers=header)
            access_token = response.json()
            return (access_token["token"], access_token["expires_at"])
        
        except requests.exceptions.HTTPError as errh:
            self.logger.log_error(f"Token retrieval HTTP Error: {errh}")
            return errh
        except requests.exceptions.ConnectionError as errc:
            self.logger.log_error(f"Token retrieval Connection Error: {errc}")
            return errc
        except requests.exceptions.Timeout as errt:
            self.logger.log_error(f"Token retrieval Timeout Error: {errt}")
            return errt
        except requests.exceptions.RequestException as err:
            self.logger.log_error(f"Token retrieval Request Exception: {err}")
            return err
        

    def make_ql_request(self, query: str, params: dict) -> tuple[str, str, str] | dict:
        """
        Makes a GraphQL request to the GitHub API using the query and parameters above

        Args:
            query - Query to be sent to API
            params - Parameters used within the query

        Returns:
            Either:
                - tuple: ("error", <error_type>, <error_message>)
                - dict: Parsed JSON response from GitHub GraphQL API
        """

        json_request = {
            'query': query,
            'variables': params
        }

        response = requests.post(url=self.api_url, json=json_request, headers=self.headers)


        if response.status_code != 200:
            self.logger.log_error(f"GitHub API Response: {response.status_code}: {response.text}")
            return ("error", response.status_code, response.text)

        response_json = response.json()

        if "errors" in response_json:
            error = response_json["errors"][0]
            error_type = error.get("type", "No Error Type")
            error_message = error.get("message", "No Error Message")

            self.logger.log_error(f"GraphQL error: {error_type}: {error_message}")

            return ("error", error_type, error_message)
        
        # Successful response
        return response_json
        

    def get_all_user_details(self) -> list | tuple:
        """
        Retrieve all the usernames within the GitHub organisation

        Returns:
            list(dict) - members usernames and emails
        """

        user_to_email = []
        email_to_user = []
        has_next_page = True
        cursor = None

        while has_next_page:
            query = '''
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
            '''

            params = {
                "org": self.org,
                "cursor": cursor
            }

            response_json = self.make_ql_request(query, params)

            org_data = response_json.get("data", {}).get("organization")

            if not org_data:
                org_error_message = f"Organisation '{self.org} not found or inaccessible'"
                self.logger.log_warning(org_error_message)
                return ("NotFound", org_error_message)
        
            members_conn = org_data.get("membersWithRole", {})
            page_info = members_conn.get("pageInfo", {})
            has_next_page = page_info.get("hasNextPage", False)
            cursor = page_info.get("endCursor")

            for node in members_conn.get("nodes", []):
                username = node.get('login')
                email = node.get('organizationVerifiedDomainEmails', [])

                user_to_email.append({
                    username: email,
                })

                for address in email:
                    email_to_user.append({
                        address: username,
                    })       

        return user_to_email, email_to_user
    