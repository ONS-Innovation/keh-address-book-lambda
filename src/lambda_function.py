"""
AWS Lambda handler for the KEH Test Data Generator
"""

import json

from logger import wrapped_logging
import boto3
from s3writer import S3Writer
from github_services import GitHubServices
from dotenv import load_dotenv
import os

from keh_teams_alert import TeamsAlertClient

# Load environment variables from .env file
load_dotenv()


def lambda_handler(event, context):
    """
    AWS Lambda handler function for generating synthetic test data.

    Args:
        event: Input event data (dict)
        context: Lambda context object

    Raises:
        Exception: If secret manager or s3client are None
        Exception: If the environmental variables are not found
        Exception: If there was a failure writing to S3

    Returns:
        dict: Response with statusCode and generated data
    """

    org = os.getenv("GITHUB_ORG")
    bucket_name = os.getenv("S3_BUCKET_NAME")
    github_client_id_secret_name = os.getenv("GITHUB_CLIENT_ID_SECRET_NAME")
    github_private_key_secret_name = os.getenv("GITHUB_PRIVATE_KEY_SECRET_NAME")
    alert_secret_name = os.getenv("ALERT_SECRET_NAME")

    # Validate environment variables are set
    if not org:
        raise Exception("GITHUB_ORG environment variable not set")
    if not bucket_name:
        raise Exception("S3_BUCKET_NAME environment variable not set")
    if not github_client_id_secret_name:
        raise Exception("GITHUB_CLIENT_ID_SECRET_NAME environment variable not set")
    if not github_private_key_secret_name:
        raise Exception("GITHUB_PRIVATE_KEY_SECRET_NAME environment variable not set")
    if not alert_secret_name:
        raise Exception("ALERT_SECRET_NAME environment variable not set")

    logger = wrapped_logging(False)

    try:
        secret_manager = boto3.client("secretsmanager")
        s3_client = boto3.client("s3")
    except Exception:
        secret_manager = None
        s3_client = None

    if secret_manager is None or s3_client is None:
        message = f"Unable to retrieve Secret Manager ({'empty' if secret_manager is None else 'Not empty'}) or S3Client({'empty' if s3_client is None else 'Not empty'})"
        logger.log_error(message)
        raise Exception(message)

    # Get GitHub Credentials from Secrets Manager
    github_client_id_secret = secret_manager.get_secret_value(
        SecretId=github_client_id_secret_name
    )
    github_client_id = json.loads(github_client_id_secret["SecretString"]).get(
        "ClientID"
    )

    github_private_key_secret = secret_manager.get_secret_value(
        SecretId=github_private_key_secret_name
    )
    github_private_key = github_private_key_secret["SecretString"]

    if not github_client_id or not github_private_key:
        message = "GitHub Client ID or Private Key not found in Secrets Manager"
        logger.log_error(message)
        raise Exception(message)

    github_services = GitHubServices(org, logger, github_client_id, github_private_key)
    s3writer = S3Writer(logger, s3_client, bucket_name)

    # Initialise alert service
    alert_secrets = secret_manager.get_secret_value(SecretId=alert_secret_name)
    alert_secrets_dict = json.loads(alert_secrets["SecretString"])

    # Verify required secret values are present
    required_keys = [
        "azure_tenant_id",
        "azure_client_id",
        "azure_client_secret",
        "azure_webhook_url",
        "channel_id",
    ]
    for key in required_keys:
        if key not in alert_secrets_dict:
            raise Exception(f"Missing required alert secret key: {key}")

    channel_id = alert_secrets_dict.get("channel_id")
    azure_webhook_url = alert_secrets_dict.get("azure_webhook_url")

    alerts_client = TeamsAlertClient(
        tenant_id=alert_secrets_dict.get("azure_tenant_id"),
        client_id=alert_secrets_dict.get("azure_client_id"),
        client_secret=alert_secrets_dict.get("azure_client_secret"),
        scope="https://management.azure.com/.default",
    )

    # Fetch data from GitHub
    try:
        response = github_services.get_all_user_details()

        if response[0] == "NotFound":
            return {
                "statusCode": 404,
                "body": json.dumps(
                    {
                        "message": "Organisation not found",
                        "error": str(response[1]),
                    }
                ),
            }
        else:
            user_to_email, email_to_user, user_to_id = response

    except Exception as e:
        alerts_client.post_to_webhook(
            webhook_url=azure_webhook_url,
            payload={
                "channel": channel_id,
                "message": f"<b>Address Book Error 🚨</b><br>Failed to fetch data from GitHub: {str(e)}. Are the environment variables set correctly?",
            },
        )
        raise Exception(
            f"Failed to fetch data from GitHub: {str(e)}. Are the environment variables set correctly?"
        )

    # Serialize and write to S3
    try:
        username_key = "addressBookUsernameKey.json"
        email_key = "addressBookEmailKey.json"
        id_key = "addressBookIDKey.json"
        folder = "AddressBook/"

        s3writer.write_data_to_s3(
            folder + username_key, json.dumps(user_to_email, indent=2)
        )
        s3writer.write_data_to_s3(
            folder + email_key, json.dumps(email_to_user, indent=2)
        )
        s3writer.write_data_to_s3(folder + id_key, json.dumps(user_to_id, indent=2))
    except Exception as e:
        alerts_client.post_to_webhook(
            webhook_url=azure_webhook_url,
            payload={
                "channel": channel_id,
                "message": f"<b>Address Book Error 🚨</b><br>Failed to write data to S3: {str(e)}.",
            },
        )
        raise Exception(f"Failed to write data to S3: {str(e)}")

    alerts_client.post_to_webhook(
        webhook_url=azure_webhook_url,
        payload={
            "channel": channel_id,
            "message": f"<b>Address Book</b><br>Successfully generated and stored address book data with a total of {len(user_to_email)} entries.",
        },
    )

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": "Successfully generated and stored address book data",
                "user_entries": len(user_to_email),
            }
        ),
    }


# This is for Development use only to allow local running of this code.

# if __name__ == "__main__":
#     print(lambda_handler(event={}, context=None))
