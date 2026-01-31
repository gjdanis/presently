"""Photo upload router."""

import os
import uuid

import boto3
from botocore.exceptions import ClientError
from common.logger import setup_logger
from common.models import AuthenticatedUser
from dependencies.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException, status

logger = setup_logger(__name__)

router = APIRouter()


@router.post("/upload")
async def get_presigned_upload_url(current_user: AuthenticatedUser = Depends(get_current_user)):
    """
    Generate a presigned URL for uploading a photo to S3.

    The frontend will use this URL to upload directly to S3,
    then include the file URL when creating/updating a wishlist item.
    """
    user_id = str(current_user.sub)
    bucket_name = os.environ.get("PHOTOS_BUCKET")
    region = os.environ.get("AWS_REGION", "us-east-1")

    if not bucket_name:
        logger.error("PHOTOS_BUCKET environment variable not set")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Photo storage is not configured",
        )

    # Generate unique filename
    file_key = f"uploads/{user_id}/{uuid.uuid4()}.jpg"

    try:
        # Create S3 client with correct region
        region = os.environ.get("AWS_REGION", "us-east-1")
        s3_client = boto3.client("s3", region_name=region)

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

        # Generate S3 URI for database storage
        s3_uri = f"s3://{bucket_name}/{file_key}"

        # Generate presigned GET URL for immediate preview (1 hour expiry)
        preview_url = s3_client.generate_presigned_url(
            "get_object", Params={"Bucket": bucket_name, "Key": file_key}, ExpiresIn=3600
        )

        return {
            "upload_url": presigned_post["url"],
            "fields": presigned_post["fields"],
            "file_url": s3_uri,  # S3 URI to save in database
            "preview_url": preview_url,  # HTTP URL for immediate display
        }

    except ClientError as e:
        logger.exception("ClientError generating upload URL")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate upload URL: {str(e)}",
        ) from e
    except Exception as e:
        logger.exception("Unexpected error generating upload URL")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        ) from e
