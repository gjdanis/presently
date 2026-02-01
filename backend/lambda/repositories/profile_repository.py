"""Profile repository - handles all database operations for user profiles."""

from datetime import datetime
from uuid import UUID

from common.db import execute_insert, execute_query
from common.logger import setup_logger
from pydantic import BaseModel

logger = setup_logger(__name__)


# Domain models
class ProfileEntity(BaseModel):
    """Profile entity from database."""

    id: UUID
    email: str
    name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProfileRepository:
    """Repository for profile data access."""

    def get_profile_by_id(self, user_id: str) -> ProfileEntity | None:
        """Get user profile by ID."""
        query = """
            SELECT id, email, name, created_at, updated_at
            FROM profiles
            WHERE id = %s
        """
        result = execute_query(query, (user_id,), fetch_one=True)
        return ProfileEntity(**result) if result else None

    def update_profile(self, user_id: str, name: str | None = None) -> ProfileEntity | None:
        """Update user profile. Returns updated profile."""
        updates = []
        params = []

        if name is not None:
            updates.append("name = %s")
            params.append(name)

        if not updates:
            # No fields to update, just return current profile
            return self.get_profile_by_id(user_id)

        params.append(user_id)

        query = f"""
            UPDATE profiles
            SET {', '.join(updates)}
            WHERE id = %s
            RETURNING id, email, name, created_at, updated_at
        """

        result = execute_query(query, tuple(params), fetch_one=True)
        return ProfileEntity(**result) if result else None

    def create_profile(self, user_id: str, email: str, name: str) -> ProfileEntity | None:
        """Create a new profile (typically from Cognito post-confirmation)."""
        query = """
            INSERT INTO profiles (id, email, name)
            VALUES (%s, %s, %s)
            ON CONFLICT (id) DO NOTHING
            RETURNING id, email, name, created_at, updated_at
        """
        result = execute_insert(query, (user_id, email, name))
        return ProfileEntity(**result) if result else None
