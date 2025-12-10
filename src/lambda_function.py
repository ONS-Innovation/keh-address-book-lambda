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


# TODO: 
# * 2. go through logic...
# * 3. Ensure it works locally
# * 4. Setup tests
# * 5. Setup and Update mkdocs 

# ! LOGIC:
# * Set up logger
# * Create S3writer class and the Github Service class (making sure to pass through the logger into init)
# * retrieve the email and username data from Github service GraphQL API request (pagination, error handling)
# * Format it into json, "'username': username, 'email': email"
# * pass that into the S3 writer, to upload to file

# FOR LAMBDA DEV
# # Load environment variables from .env file
# load_dotenv()

# FOR LOCAL DEV
# Load environment variables from .env file
load_dotenv(find_dotenv())


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

    secret_manager = boto3.client("secretsmanager")

    logger = wrapped_logging(False)
    github_services = GitHubServices(org, logger, secret_manager, secret_name, app_client_id)
    s3writer = S3Writer(logger)

    user_to_email, email_to_user = github_services.get_all_user_details()

    user_to_email = json.dumps(user_to_email, indent=2)
    email_to_user = json.dumps(email_to_user, indent=2)

    s3writer.write_data_to_s3("addressBookUsernameKey.json", user_to_email)
    s3writer.write_data_to_s3("addressBookEmailKey.json", email_to_user)

        
        # return {
        #     'statusCode': 500,
        #     'body': json.dumps({
        #         'message': 'Error generating data',
        #         'error': str(e)
        #     }),
        #     'extra': f"{data_type} {entries}"
        # }


if __name__ == "__main__":
    # Simple local runner to invoke the handler
    # Note: Requires AWS creds and env vars to be set
    try:
        result = lambda_handler(event={}, context=None)
        if result is not None:
            print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error running lambda_handler locally: {e}")
