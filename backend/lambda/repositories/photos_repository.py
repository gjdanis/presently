"""Photos repository - handles S3 operations for photo uploads."""

import os
import uuid

import boto3
from common.logger import setup_logger
from pydantic import BaseModel

logger = setup_logger(__name__)


# Domain models
class PresignedUploadResult(BaseModel):
    """Presigned upload URL result."""

    upload_url: str
    fields: dict
    file_url: str  # S3 URI for database storage
    preview_url: str  # HTTP URL for immediate display

    class Config:
        from_attributes = True


class PhotosRepository:
    """Repository for photo S3 operations."""

    def __init__(self):
        """Initialize S3 client."""
        self.region = os.environ.get("AWS_REGION", "us-east-1")
        self.bucket_name = os.environ.get("PHOTOS_BUCKET")
        self.s3_client = None

        if self.bucket_name:
            self.s3_client = boto3.client("s3", region_name=self.region)

    def generate_presigned_upload_url(self, user_id: str) -> PresignedUploadResult:
        """Generate presigned URL for uploading a photo to S3."""
        if not self.bucket_name:
            raise ValueError("PHOTOS_BUCKET environment variable not set")

        if not self.s3_client:
            raise ValueError("S3 client not initialized")

        # Generate unique filename
        file_key = f"uploads/{user_id}/{uuid.uuid4()}.jpg"

        # Generate presigned POST URL (allows file upload)
        presigned_post = self.s3_client.generate_presigned_post(
            Bucket=self.bucket_name,
            Key=file_key,
            Fields={"Content-Type": "image/jpeg"},
            Conditions=[
                {"Content-Type": "image/jpeg"},
                ["content-length-range", 0, 5242880],  # Max 5MB
            ],
            ExpiresIn=3600,  # 1 hour
        )

        # Generate S3 URI for database storage
        s3_uri = f"s3://{self.bucket_name}/{file_key}"

        # Generate presigned GET URL for immediate preview (1 hour expiry)
        preview_url = self.s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": file_key},
            ExpiresIn=3600,
        )

        return PresignedUploadResult(
            upload_url=presigned_post["url"],
            fields=presigned_post["fields"],
            file_url=s3_uri,
            preview_url=preview_url,
        )
