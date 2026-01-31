"""Profile management FastAPI router."""

from typing import Any

from common.db import execute_insert, execute_query
from common.logger import setup_logger
from common.models import AuthenticatedUser, ProfileResponse, ProfileUpdate
from dependencies.auth import get_current_user
from fastapi import APIRouter, Depends, HTTPException, status

logger = setup_logger(__name__)

router = APIRouter()


@router.get("", response_model=ProfileResponse)
async def get_profile(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ProfileResponse:
    """Get the current user's profile."""
    user_id = str(current_user.sub)

    query = """
        SELECT id, email, name, created_at, updated_at
        FROM profiles
        WHERE id = %s
    """

    result = execute_query(query, (user_id,), fetch_one=True)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )

    return ProfileResponse(**result)


@router.put("", response_model=ProfileResponse)
async def update_profile(
    update_data: ProfileUpdate,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ProfileResponse:
    """Update the current user's profile."""
    user_id = str(current_user.sub)

    # Build dynamic UPDATE query based on provided fields
    updates = []
    params: list[Any] = []

    if update_data.name is not None:
        updates.append("name = %s")
        params.append(update_data.name)

    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )

    params.append(user_id)

    query = f"""
        UPDATE profiles
        SET {', '.join(updates)}
        WHERE id = %s
        RETURNING id, email, name, created_at, updated_at
    """

    result = execute_query(query, tuple(params), fetch_one=True)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )

    return ProfileResponse(**result)


def create_profile_from_cognito(user_id: str, email: str, name: str) -> dict[str, Any] | None:
    """
    Create a profile when a user signs up via Cognito.
    This is typically called from a Cognito post-confirmation Lambda trigger.

    Args:
        user_id: Cognito User Sub (UUID)
        email: User email
        name: User name

    Returns:
        Profile dict or None if creation failed
    """
    query = """
        INSERT INTO profiles (id, email, name)
        VALUES (%s, %s, %s)
        ON CONFLICT (id) DO NOTHING
        RETURNING id, email, name, created_at, updated_at
    """

    result = execute_insert(query, (user_id, email, name))
    return result
