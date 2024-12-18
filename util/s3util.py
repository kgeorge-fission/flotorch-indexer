import json
import logging
import boto3
import io
from botocore.exceptions import ClientError
from urllib.parse import urlparse
import csv
import pandas as pd
from typing import Optional, List, Dict


class S3Util:
    """Utility class for reading JSON data from AWS S3 and converting it to dictionary."""
    
    def __init__(self):
        """Initialize S3 client."""
        self.s3_client = boto3.client('s3')
        self.logger = logging.getLogger(__name__)

    def read_json_from_s3(self, s3_path: str) -> Optional[Dict]:
        """
        Read JSON data from S3 and convert it to a dictionary.

        Args:
            bucket_name (str): Name of the S3 bucket
            key (str): Object key (path) in the S3 bucket

        Returns:
            Optional[Dict]: Dictionary containing the JSON data if successful, None otherwise

        Raises:
            ClientError: If there's an error accessing S3
            json.JSONDecodeError: If the content cannot be parsed as JSON
        """
        try:
            bucket_name, object_key = self.parse_s3_path(s3_path)
            
            # Get the object from S3
            response = self.s3_client.get_object(
                Bucket=bucket_name,
                Key=object_key
            )
            
            # Read the data and decode it
            file_content = response['Body'].read().decode('utf-8')
            
            # Parse JSON content
            json_content = json.loads(file_content)
            
            return json_content

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_message = e.response.get('Error', {}).get('Message', 'Unknown error')
            self.logger.error(
                f"Failed to read from S3: {error_code} - {error_message}",
                exc_info=True
            )
            raise

        except json.JSONDecodeError as e:
            self.logger.error(
                f"Failed to parse JSON content from {bucket_name}/{key}",
                exc_info=True
            )
            raise

        except Exception as e:
            self.logger.error(
                f"Unexpected error reading from S3: {str(e)}",
                exc_info=True
            )
            raise

    def read_csv_from_s3(self, object_key: str, bucket_name: str, as_dataframe: bool = False) -> Optional[object]:
        """
        Read CSV data from S3 and convert it to a list of dictionaries or a pandas DataFrame.

        Args:
            s3_path (str): S3 path in the format s3://bucket-name/path/to/object
            as_dataframe (bool): If True, return a pandas DataFrame, otherwise return a list of dictionaries.

        Returns:
            Optional[object]: List of dictionaries or pandas DataFrame containing the CSV data if successful, None otherwise.

        Raises:
            ClientError: If there's an error accessing S3.
            csv.Error: If the content cannot be parsed as CSV.
        """
        try:
            
            self.logger.info(bucket_name + "--" + object_key)
            # Get the object from S3
            response = self.s3_client.get_object(
                Bucket=bucket_name,
                Key=object_key
            )

            # Read the data
            file_content = response['Body'].read().decode('utf-8')

            if as_dataframe:
                # Parse content into a pandas DataFrame
                csv_data = pd.read_csv(io.StringIO(file_content))
            else:
                # Parse content into a list of dictionaries
                csv_reader = csv.DictReader(file_content.splitlines())
                csv_data = [row for row in csv_reader]

            return csv_data
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_message = e.response.get('Error', {}).get('Message', 'Unknown error')
            self.logger.error(
                f"Failed to read from S3: {error_code} - {error_message}",
                exc_info=True
            )
            raise

        except csv.Error as e:
            self.logger.error(
                f"Failed to parse CSV content from {bucket_name}/{object_key}",
                exc_info=True
            )
            raise

        except Exception as e:
            self.logger.error(
                f"Unexpected error reading from S3: {str(e)}",
                exc_info=True
            )
            raise

    def read_json_and_content_from_s3(self, s3_path: str) -> Optional[Dict]:
        """
        Read JSON data from S3 and convert it to a dictionary.

        Args:
            bucket_name (str): Name of the S3 bucket
            key (str): Object key (path) in the S3 bucket

        Returns:
            Optional[Dict]: Dictionary containing the JSON data if successful, None otherwise

        Raises:
            ClientError: If there's an error accessing S3
            json.JSONDecodeError: If the content cannot be parsed as JSON
        """
        try:
            bucket_name, object_key = self.parse_s3_path(s3_path)

            # Get the object from S3
            response = self.s3_client.get_object(
                Bucket=bucket_name,
                Key=object_key
            )

            # Read the data and decode it
            file_content = response['Body'].read().decode('utf-8')

            # Parse JSON content
            json_content = json.loads(file_content)

            return json_content, file_content

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_message = e.response.get('Error', {}).get('Message', 'Unknown error')
            self.logger.error(
                f"Failed to read from S3: {error_code} - {error_message}",
                exc_info=True
            )
            raise

        except json.JSONDecodeError as e:
            self.logger.error(
                f"Failed to parse JSON content from {bucket_name}/{key}",
                exc_info=True
            )
            raise

        except Exception as e:
            self.logger.error(
                f"Unexpected error reading from S3: {str(e)}",
                exc_info=True
            )
            raise
    
    def parse_s3_path(self, s3_path: str) -> tuple[str, str]:
        """
        Parse S3 path into bucket and key.
        
        Args:
            s3_path: Full S3 path (e.g., 's3://bucket-name/path/to/file.csv')
            
        Returns:
            tuple: (bucket_name, object_key)
            
        Raises:
            ValueError: If S3 path is invalid
        """
        if not s3_path.startswith('s3://'):
            raise ValueError("S3 path must start with 's3://'")
        
        path = s3_path.replace('s3://', '')
        parts = path.split('/', 1)
        
        if len(parts) < 2:
            raise ValueError("Invalid S3 path format")
        
        return parts[0], parts[1]
    

    def download_file_from_s3(self, s3_path: str, local_path: str = '/tmp/downloaded_file.pdf') -> str:
        """Download file from S3 using a full S3 path and return the local path."""
        
        try:
            parsed_url = urlparse(s3_path)
            bucket = parsed_url.netloc
            key = parsed_url.path.lstrip('/')

            self.logger.info(f"Downloading file from S3: bucket={bucket}, key={key}")
            self.s3_client.download_file(Bucket=bucket, Key=key, Filename=local_path)
            self.logger.info("Download successful.")
            return local_path
        except Exception as e:
            self.logger.error(f"Failed to download file from S3: {e}")
            raise

