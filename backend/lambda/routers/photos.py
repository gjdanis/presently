"""Photo upload router."""

from common.logger import setup_logger
from common.models import AuthenticatedUser, PresignedUrlResponse
from dependencies.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException, status
from services.groups_service import BadRequestError
from services.photos_service import PhotosService

logger = setup_logger(__name__)

router = APIRouter()


def get_photos_service() -> PhotosService:
    """Dependency to get photos service instance."""
    return PhotosService()


@router.post("/upload", response_model=PresignedUrlResponse)
async def get_presigned_upload_url(
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: PhotosService = Depends(get_photos_service),
):
    """
    Generate a presigned URL for uploading a photo to S3.

    The frontend will use this URL to upload directly to S3,
    then include the file URL when creating/updating a wishlist item.
    """
    user_id = str(current_user.sub)

    try:
        return service.get_presigned_upload_url(user_id)
    except BadRequestError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e
