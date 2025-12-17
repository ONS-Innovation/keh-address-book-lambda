"""This file contains the S3Writer class to weekly upload the GitHub usernames and ONS emails to S3

Typical usage example:

    s3writer = S3Writer(logger)
    s3writer.write_data_to_s3(file_to_update, data) # These are the filename of the updated file and its contents respectively
"""

import json
from typing import Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class S3Writer:
    """
    A class for uploading updated GitHub username and ONS emails to an AWS S3 Bucket

    This class provides a setup and then can be used for all uploading throughout the programs lifecycle.

    Atrributes:
        s3_resrouce: The established 'session' or connection to AWS servers
        bucket_name: The name of the bucket to store the new JSON files
        logger: The variable which connects to the logger class

    Methods:
        write_data_to_s3: Allows the program to connect to the S3 bucket and upload the JSON
    """

    def __init__(self, logger, s3_client, bucket_name):
        """
        Initialises the S3Writer.
        """
        self.logger = logger
        self.s3_client = s3_client

        # Load bucket name from environment variable
        self.bucket_name = bucket_name
        if not self.bucket_name:
            raise ValueError(
                "S3_BUCKET_NAME environment variable is not set."
                "Please create a .env file with S3_BUCKET_NAME=your-bucket-name"
            )

    def write_data_to_s3(
        self, file_to_update: str | None, data: dict[str, Any] | str | None
    ):
        """
        Writes the data to a specific filename within the specificed s3 bucket

        Args:
            file_to_update: Name of the file to update within S3
            data: Contents of the new and updated file
        """

        # Ensure that the arguments are not None
        if file_to_update is None or data is None:
            self.logger.log_error(
                f"filename or data is empty. filename: {'empty' if file_to_update is None else 'filled'}, data: {'empty' if data is None else 'filled'}"
            )
            return

        # Convert dict to JSON string if needed
        if isinstance(data, dict):
            data_str = json.dumps(data, indent=2)
        else:
            data_str = data

        # Upload the file to S3 within the bucket directly
        key = f"{file_to_update}"

        try:

            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=(
                    data_str.encode("utf-8")
                    if isinstance(data_str, str)
                    else json.dumps(data_str).encode("utf-8")
                ),
                ContentType="application/json",
            )

        except Exception as error:
            self.logger.log_error(
                f"Unable to upload updated username and email data to S3, {error}"
            )
        else:
            self.logger.log_info(
                "Successfully uploaded updated username and email data to S3"
            )
