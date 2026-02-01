"""Profile management FastAPI router."""

from common.logger import setup_logger
from common.models import AuthenticatedUser, ProfileResponse, ProfileUpdate
from dependencies.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException, status
from services.groups_service import BadRequestError, NotFoundError
from services.profile_service import ProfileService

logger = setup_logger(__name__)

router = APIRouter()


def get_profile_service() -> ProfileService:
    """Dependency to get profile service instance."""
    return ProfileService()


@router.get("", response_model=ProfileResponse)
async def get_profile(
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
) -> ProfileResponse:
    """Get the current user's profile."""
    user_id = str(current_user.sub)

    try:
        return service.get_profile(user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.put("", response_model=ProfileResponse)
async def update_profile(
    update_data: ProfileUpdate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: ProfileService = Depends(get_profile_service),
) -> ProfileResponse:
    """Update the current user's profile."""
    user_id = str(current_user.sub)

    try:
        return service.update_profile(user_id, update_data.name)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except BadRequestError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


def create_profile_from_cognito(user_id: str, email: str, name: str) -> ProfileResponse | None:
    """
    Create a profile when a user signs up via Cognito.
    This is typically called from a Cognito post-confirmation Lambda trigger.

    Args:
        user_id: Cognito User Sub (UUID)
        email: User email
        name: User name

    Returns:
        ProfileResponse or None if creation failed
    """
    service = ProfileService()
    return service.create_profile_from_cognito(user_id, email, name)
