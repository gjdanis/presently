"""Photo upload Lambda handler."""

import os
import uuid
from typing import Any

import boto3
from botocore.exceptions import ClientError

from common.auth import require_auth
from common.decorators import handle_cors
from common.models import PresignedUrlResponse
from common.responses import created, error, server_error


@handle_cors("POST,OPTIONS")
def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Handle /photos/* endpoints."""
    http_method = event["httpMethod"]
    path = event["path"]

    # Require authentication
    user, auth_error = require_auth(event)
    if not user:
        return auth_error

    # Route to appropriate function
    if http_method == "POST" and path == "/photos/upload":
        return get_presigned_upload_url(str(user.sub))

    return error("Not Found", 404)


def get_presigned_upload_url(user_id: str) -> dict[str, Any]:
    """
    Generate a presigned URL for uploading a photo to S3.

    The frontend will use this URL to upload directly to S3,
    then include the file URL when creating/updating a wishlist item.
    """
    bucket_name = os.environ.get("PHOTOS_BUCKET")
    cdn_domain = os.environ.get("PHOTOS_CDN")

    if not bucket_name:
        return server_error("Photo storage is not configured")

    # Generate unique filename
    file_key = f"uploads/{user_id}/{uuid.uuid4()}.jpg"

    try:
        # Create S3 client
        s3_client = boto3.client("s3")

        # Generate presigned POST URL (allows file upload)
        presigned_post = s3_client.generate_presigned_post(
            Bucket=bucket_name,
            Key=file_key,
            Fields={"Content-Type": "image/jpeg"},
            Conditions=[
                {"Content-Type": "image/jpeg"},
                ["content-length-range", 0, 5242880],  # Max 5MB
            ],
            ExpiresIn=3600,  # 1 hour
        )

        # Construct the file URL (use CDN if available)
        if cdn_domain:
            file_url = f"https://{cdn_domain}/{file_key}"
        else:
            file_url = f"https://{bucket_name}.s3.amazonaws.com/{file_key}"

        return created(
            {
                "upload_url": presigned_post["url"],
                "fields": presigned_post["fields"],
                "file_url": file_url,
            }
        )

    except ClientError as e:
        return server_error(f"Failed to generate upload URL: {str(e)}")
    except Exception as e:
        return server_error(f"Unexpected error: {str(e)}")
