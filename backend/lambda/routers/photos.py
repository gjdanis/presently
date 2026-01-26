"""Photo upload router."""

import os
import uuid

import boto3
from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, HTTPException, status

from common.models import AuthenticatedUser
from dependencies.auth import get_current_user

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
    cdn_domain = os.environ.get("PHOTOS_CDN")

    if not bucket_name:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Photo storage is not configured",
        )

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

        return {
            "upload_url": presigned_post["url"],
            "fields": presigned_post["fields"],
            "file_url": file_url,
        }

    except ClientError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate upload URL: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}",
        )
