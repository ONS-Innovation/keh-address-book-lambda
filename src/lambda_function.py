"""
AWS Lambda handler for the KEH Test Data Generator
"""

import json
import os

from logger import wrapped_logging
from s3writer import S3Writer
from github_services import GitHubServices

# Optional dotenv: don't fail if not installed
try:
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()
except Exception:  # pragma: no cover
    pass

# Optional boto3 shim to keep imports working in test envs
try:
    import boto3  # type: ignore
except Exception:  # pragma: no cover - only when boto3 missing

    class _Boto3Shim:
        def client(self, name, *args, **kwargs):
            # Return a dummy object so monkeypatching or stubs can replace usage
            return object()

    boto3 = _Boto3Shim()  # type: ignore


def lambda_handler(event, context):
    """
    AWS Lambda handler function for generating synthetic test data.

    Args:
        event: Input event data (dict)
        context: Lambda context object

    Returns:
        dict: Response with statusCode and generated data
    """

    org = os.getenv("GITHUB_ORG")
    secret_name = os.getenv("AWS_SECRET_NAME")
    app_client_id = os.getenv("GITHUB_APP_CLIENT_ID")
    bucket_name = os.getenv("S3_BUCKET_NAME")

    try:
        secret_manager = boto3.client("secretsmanager")
        s3_client = boto3.client("s3")
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "message": "Failed to initialize AWS Secrets Manager or S3 client",
                    "error": str(e),
                }
            ),
        }

    logger = wrapped_logging(False)
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
            user_to_email, email_to_user = response

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

        s3writer.write_data_to_s3(username_key, json.dumps(user_to_email, indent=2))
        s3writer.write_data_to_s3(email_key, json.dumps(email_to_user, indent=2))
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


if __name__ == "__main__":
    # Simple local runner to invoke the handler
    # Note: Requires AWS creds and env vars to be set
    try:
        lambda_handler(event={}, context=None)
    except Exception as e:
        print(f"Error running lambda_handler locally: {e}")
