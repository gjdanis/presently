"""Profile service - business logic for user profile management."""

from common.logger import setup_logger
from common.models import ProfileResponse
from repositories.profile_repository import ProfileRepository

from services.groups_service import BadRequestError, NotFoundError

logger = setup_logger(__name__)


class ProfileService:
    """Service for profile business logic."""

    def __init__(self, repository: ProfileRepository | None = None):
        """Initialize service with repository."""
        self.repo = repository or ProfileRepository()

    def get_profile(self, user_id: str) -> ProfileResponse:
        """Get user profile."""
        profile = self.repo.get_profile_by_id(user_id)

        if not profile:
            raise NotFoundError("Profile not found")

        return ProfileResponse(
            id=profile.id,
            email=profile.email,
            name=profile.name,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )

    def update_profile(self, user_id: str, name: str | None = None) -> ProfileResponse:
        """Update user profile."""
        if name is None:
            raise BadRequestError("No fields to update")

        profile = self.repo.update_profile(user_id, name)

        if not profile:
            raise NotFoundError("Profile not found")

        return ProfileResponse(
            id=profile.id,
            email=profile.email,
            name=profile.name,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )

    def create_profile_from_cognito(
        self, user_id: str, email: str, name: str
    ) -> ProfileResponse | None:
        """Create a profile from Cognito post-confirmation trigger."""
        profile = self.repo.create_profile(user_id, email, name)

        if not profile:
            return None

        return ProfileResponse(
            id=profile.id,
            email=profile.email,
            name=profile.name,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )
