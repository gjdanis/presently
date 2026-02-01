"""Integration tests for ProfileService."""

from typing import Any

import pytest
from services.groups_service import BadRequestError, NotFoundError
from services.profile_service import ProfileService


@pytest.fixture
def profile_service() -> ProfileService:
    """Create a ProfileService instance."""
    return ProfileService()


def test_get_profile(
    clean_db: Any, sample_profile: dict[str, Any], profile_service: ProfileService
):
    """Test getting a user profile."""
    profile = profile_service.get_profile(sample_profile["id"])

    assert str(profile.id) == sample_profile["id"]
    assert profile.email == sample_profile["email"]
    assert profile.name == sample_profile["name"]


def test_get_profile_not_found(clean_db: Any, profile_service: ProfileService):
    """Test getting a non-existent profile."""
    from uuid import uuid4

    with pytest.raises(NotFoundError, match="not found"):
        profile_service.get_profile(str(uuid4()))


def test_update_profile(
    clean_db: Any, sample_profile: dict[str, Any], profile_service: ProfileService
):
    """Test updating a user profile."""
    updated = profile_service.update_profile(
        user_id=sample_profile["id"],
        name="Updated Name"
    )

    assert updated.name == "Updated Name"
    assert updated.email == sample_profile["email"]  # Email unchanged


def test_update_profile_no_fields(
    clean_db: Any, sample_profile: dict[str, Any], profile_service: ProfileService
):
    """Test updating profile with no fields."""
    with pytest.raises(BadRequestError, match="No fields"):
        profile_service.update_profile(
            user_id=sample_profile["id"],
            name=None
        )


def test_create_profile_from_cognito(clean_db: Any, profile_service: ProfileService):
    """Test creating a profile from Cognito."""
    from uuid import uuid4

    user_id = str(uuid4())
    email = "cognito@example.com"
    name = "Cognito User"

    profile = profile_service.create_profile_from_cognito(user_id, email, name)

    assert profile is not None
    assert str(profile.id) == user_id
    assert profile.email == email
    assert profile.name == name


def test_create_profile_from_cognito_duplicate(
    clean_db: Any, sample_profile: dict[str, Any], profile_service: ProfileService
):
    """Test creating a profile that already exists (conflict handling)."""
    # Try to create with same ID
    profile = profile_service.create_profile_from_cognito(
        sample_profile["id"],
        "different@example.com",
        "Different Name"
    )

    # Should return None due to ON CONFLICT DO NOTHING
    assert profile is None
