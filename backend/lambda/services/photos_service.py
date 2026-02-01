"""Photos service - business logic for photo upload management."""

from botocore.exceptions import ClientError
from common.logger import setup_logger
from common.models import PresignedUrlResponse
from repositories.photos_repository import PhotosRepository

from services.groups_service import BadRequestError

logger = setup_logger(__name__)


class PhotosService:
    """Service for photo upload business logic."""

    def __init__(self, repository: PhotosRepository | None = None):
        """Initialize service with repository."""
        self.repo = repository or PhotosRepository()

    def get_presigned_upload_url(self, user_id: str) -> PresignedUrlResponse:
        """
        Generate a presigned URL for uploading a photo to S3.

        The frontend will use this URL to upload directly to S3,
        then include the file URL when creating/updating a wishlist item.
        """
        try:
            result = self.repo.generate_presigned_upload_url(user_id)

            return PresignedUrlResponse(
                upload_url=result.upload_url,
                fields=result.fields,
                file_url=result.file_url,
                preview_url=result.preview_url,
            )

        except ValueError as e:
            logger.error(f"Configuration error: {str(e)}")
            raise BadRequestError(f"Photo storage is not configured: {str(e)}") from e

        except ClientError as e:
            logger.exception("ClientError generating upload URL")
            raise BadRequestError(f"Failed to generate upload URL: {str(e)}") from e

        except Exception as e:
            logger.exception("Unexpected error generating upload URL")
            raise BadRequestError(f"Unexpected error: {str(e)}") from e
