"""S3 utilities for handling photo URLs."""

import os
import re
from typing import Optional

import boto3
from botocore.exceptions import ClientError


def s3_uri_to_presigned_url(s3_uri: str, expires_in: int = 3600) -> str:
    """
    Convert an S3 URI (s3://bucket/key) to a presigned URL.

    Args:
        s3_uri: S3 URI in format s3://bucket-name/key/path
        expires_in: URL expiration time in seconds (default 1 hour, max 7 days)

    Returns:
        Presigned URL string

    Raises:
        ValueError: If s3_uri is not a valid S3 URI
    """
    # Parse S3 URI
    match = re.match(r's3://([^/]+)/(.+)', s3_uri)
    if not match:
        raise ValueError(f"Invalid S3 URI format: {s3_uri}")

    bucket_name = match.group(1)
    key = match.group(2)

    try:
        # Use AWS_REGION env var or default to us-east-1
        region = os.getenv('AWS_REGION', 'us-east-1')
        s3_client = boto3.client('s3', region_name=region)

        # Ensure expires_in doesn't exceed 7 days (S3 limit)
        expires_in = min(expires_in, 604800)

        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': key},
            ExpiresIn=expires_in
        )

        return url

    except ClientError as e:
        print(f"Error generating presigned URL for {s3_uri}: {e}")
        return None
