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
    secret_name = os.getenv("AWS_SECRET_NAME")
    app_client_id = os.getenv("GITHUB_APP_CLIENT_ID")
    bucket_name = os.getenv("S3_BUCKET_NAME")

    logger = wrapped_logging(False)

    try:
        secret_manager = boto3.client("secretsmanager")
        s3_client = boto3.client("s3")
    except Exception:
        secret_manager = None
        s3_client = None

    if secret_manager is None or s3_client is None:
        message = f"Unable to retrieve Secret Manager ({'empty' if secret_manager is None else 'Not empty'}) or S3Client({'empty' if secret_manager is None else 'Not empty'})"
        logger.log_error(message)
        raise Exception(message)

    github_services = GitHubServices(
        org, logger, secret_manager, secret_name, app_client_id
    )
    s3writer = S3Writer(logger, s3_client, bucket_name)

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
        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "message": "Missing required environment variables",
                    "error": str(e),
                }
            ),
        }

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
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "Failed to write data to S3", "error": str(e)}
            ),
        }

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
#     try:
#         lambda_handler(event={}, context=None)
#     except Exception as e:
#         print(f"Error running lambda_handler locally: {e}")
