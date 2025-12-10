"""
AWS Lambda handler for the KEH Test Data Generator
"""

import json

from logger import wrapped_logging
import boto3
from s3writer import S3Writer
from github_services import GitHubServices 
from dotenv import load_dotenv, find_dotenv
import os


# Load environment variables from .env file
load_dotenv()


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

    # Fail fast if required env vars are missing
    missing = [name for name, val in {
        "GITHUB_ORG": org,
        "AWS_SECRET_NAME": secret_name,
        "GITHUB_APP_CLIENT_ID": app_client_id,
    }.items() if not val]
    if missing:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Missing required environment variables',
                'missing': missing
            })
        }

    try:
        secret_manager = boto3.client("secretsmanager")
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Failed to initialize AWS Secrets Manager client',
                'error': str(e)
            })
        }

    logger = wrapped_logging(False)
    github_services = GitHubServices(org, logger, secret_manager, secret_name, app_client_id)
    s3writer = S3Writer(logger)

    # Fetch data from GitHub
    try:
        user_to_email, email_to_user = github_services.get_all_user_details()
    except Exception as e:
        return {
            'statusCode': 502,
            'body': json.dumps({
                'message': 'Failed to fetch user details from GitHub',
                'error': str(e)
            })
        }

    # Serialize and write to S3
    try:
        username_key = "addressBookUsernameKey.json"
        email_key = "addressBookEmailKey.json"

        s3writer.write_data_to_s3(username_key, json.dumps(user_to_email, indent=2))
        s3writer.write_data_to_s3(email_key, json.dumps(email_to_user, indent=2))
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': 'Failed to write data to S3',
                'error': str(e)
            })
        }

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Successfully generated and stored address book data',
        })
    }


if __name__ == "__main__":
    # Simple local runner to invoke the handler
    # Note: Requires AWS creds and env vars to be set
    try:
        lambda_handler(event={}, context=None)
    except Exception as e:
        print(f"Error running lambda_handler locally: {e}")
