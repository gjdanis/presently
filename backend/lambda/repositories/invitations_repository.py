"""Invitations repository - handles all database operations for group invitations."""

from datetime import datetime
from uuid import UUID

from common.db import execute_delete, execute_insert, execute_query, execute_update
from common.logger import setup_logger
from pydantic import BaseModel

logger = setup_logger(__name__)


# Domain models
class InvitationEntity(BaseModel):
    """Invitation entity from database."""

    group_id: UUID
    group_name: str
    group_description: str | None
    role: str
    expires_at: datetime | None
    accepted_at: datetime | None
    inviter_name: str
    inviter_email: str

    class Config:
        from_attributes = True


class InvitationCreateResult(BaseModel):
    """Result of creating an invitation."""

    id: UUID
    token: str

    class Config:
        from_attributes = True


class GroupDetailsEntity(BaseModel):
    """Group details for invitation creation."""

    name: str
    description: str | None
    user_role: str

    class Config:
        from_attributes = True


class UserProfileEntity(BaseModel):
    """User profile entity."""

    id: UUID
    name: str
    email: str

    class Config:
        from_attributes = True


class InvitationAcceptEntity(BaseModel):
    """Invitation details for accepting."""

    group_id: UUID
    email: str | None
    role: str
    accepted_at: datetime | None
    expires_at: datetime | None
    user_email: str | None
    max_uses: int | None
    current_uses: int

    class Config:
        from_attributes = True


class InvitationAcceptanceEntity(BaseModel):
    """Invitation acceptance record."""

    user_id: UUID
    user_name: str
    accepted_at: datetime

    class Config:
        from_attributes = True


class InvitationsRepository:
    """Repository for invitations data access."""

    def get_group_details_for_user(
        self, user_id: str, group_id: str
    ) -> GroupDetailsEntity | None:
        """Get group details and user's role."""
        query = """
            SELECT g.name, g.description, gm.role as user_role
            FROM groups g
            JOIN group_memberships gm ON g.id = gm.group_id
            WHERE gm.user_id = %s AND gm.group_id = %s
        """
        result = execute_query(query, (user_id, group_id), fetch_one=True)
        return GroupDetailsEntity(**result) if result else None

    def is_user_already_member(self, group_id: str, email: str) -> bool:
        """Check if user with email is already a member of the group."""
        query = """
            SELECT 1 FROM group_memberships gm
            JOIN profiles p ON gm.user_id = p.id
            WHERE gm.group_id = %s AND p.email = %s
        """
        result = execute_query(query, (group_id, email), fetch_one=True)
        return result is not None

    def has_pending_invitation(self, group_id: str, email: str) -> bool:
        """Check if there's already a pending invitation for this email."""
        query = """
            SELECT 1 FROM group_invitations
            WHERE group_id = %s AND email = %s AND accepted_at IS NULL
        """
        result = execute_query(query, (group_id, email), fetch_one=True)
        return result is not None

    def get_user_by_email(self, email: str) -> UserProfileEntity | None:
        """Get user profile by email."""
        query = "SELECT id, name, email FROM profiles WHERE email = %s"
        result = execute_query(query, (email,), fetch_one=True)
        return UserProfileEntity(**result) if result else None

    def get_user_profile(self, user_id: str) -> UserProfileEntity | None:
        """Get user profile by ID."""
        query = "SELECT id, name, email FROM profiles WHERE id = %s"
        result = execute_query(query, (user_id,), fetch_one=True)
        return UserProfileEntity(**result) if result else None

    def create_invitation(
        self,
        group_id: str,
        invited_by: str,
        role: str,
        token: str,
        max_uses: int | None = None,
        expires_at: datetime | None = None,
    ) -> InvitationCreateResult | None:
        """Create a new invitation (all invitations are now multi-use)."""
        query = """
            INSERT INTO group_invitations
            (group_id, invited_by, role, token, max_uses, expires_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, token
        """
        result = execute_insert(
            query, (group_id, invited_by, role, token, max_uses, expires_at)
        )
        return InvitationCreateResult(**result) if result else None

    def get_invitation_by_token(self, token: str) -> InvitationEntity | None:
        """Get invitation details by token."""
        query = """
            SELECT gi.group_id, g.name as group_name, g.description as group_description,
                   gi.role, gi.expires_at, NULL::timestamptz as accepted_at,
                   p.name as inviter_name, p.email as inviter_email
            FROM group_invitations gi
            JOIN groups g ON gi.group_id = g.id
            JOIN profiles p ON gi.invited_by = p.id
            WHERE gi.token = %s
        """
        result = execute_query(query, (token,), fetch_one=True)
        return InvitationEntity(**result) if result else None

    def get_invitation_for_accept(
        self, user_id: str | None, token: str
    ) -> InvitationAcceptEntity | None:
        """Get invitation details for accepting (multi-use invitations)."""
        query = """
            SELECT gi.group_id, NULL::text as email, gi.role, NULL::timestamptz as accepted_at, gi.expires_at,
                   p.email as user_email, gi.max_uses, gi.current_uses
            FROM group_invitations gi
            LEFT JOIN profiles p ON p.id = %s::uuid
            WHERE gi.token = %s
        """
        result = execute_query(query, (user_id, token), fetch_one=True)
        return InvitationAcceptEntity(**result) if result else None

    def is_user_group_member(self, user_id: str, group_id: str) -> bool:
        """Check if user is already a member of the group."""
        query = """
            SELECT 1 FROM group_memberships
            WHERE user_id = %s AND group_id = %s
        """
        result = execute_query(query, (user_id, group_id), fetch_one=True)
        return result is not None

    def add_user_to_group(self, user_id: str, group_id: str, role: str) -> UUID | None:
        """Add user to group with specified role."""
        query = """
            INSERT INTO group_memberships (user_id, group_id, role)
            VALUES (%s, %s, %s)
            RETURNING id
        """
        result = execute_insert(query, (user_id, group_id, role))
        return result["id"] if result else None

    def mark_invitation_accepted(self, token: str) -> None:
        """Mark invitation as accepted."""
        execute_update("UPDATE group_invitations SET accepted_at = NOW() WHERE token = %s", (token,))

    def get_user_role_in_group(self, user_id: str, group_id: str) -> str | None:
        """Get user's role in a group."""
        query = """
            SELECT role FROM group_memberships
            WHERE user_id = %s AND group_id = %s
        """
        result = execute_query(query, (user_id, group_id), fetch_one=True)
        return result["role"] if result else None

    def remove_user_from_group(self, user_id: str, group_id: str) -> int:
        """Remove user from group. Returns number of rows deleted."""
        query = """
            DELETE FROM group_memberships
            WHERE user_id = %s AND group_id = %s
        """
        return execute_delete(query, (user_id, group_id))

    def record_invitation_acceptance(
        self, invitation_id: str, user_id: str
    ) -> UUID | None:
        """Record that a user accepted a multi-use invitation."""
        query = """
            INSERT INTO invitation_acceptances (invitation_id, user_id)
            VALUES (%s, %s)
            ON CONFLICT (invitation_id, user_id) DO NOTHING
            RETURNING id
        """
        result = execute_insert(query, (invitation_id, user_id))
        return result["id"] if result else None

    def increment_invitation_uses(self, token: str) -> None:
        """Increment the usage counter for a multi-use invitation."""
        execute_update(
            "UPDATE group_invitations SET current_uses = current_uses + 1 WHERE token = %s",
            (token,),
        )

    def get_invitation_id_by_token(self, token: str) -> UUID | None:
        """Get invitation ID by token."""
        query = "SELECT id FROM group_invitations WHERE token = %s"
        result = execute_query(query, (token,), fetch_one=True)
        return result["id"] if result else None

    def has_user_accepted_invitation(self, invitation_id: str, user_id: str) -> bool:
        """Check if user has already accepted this specific invitation."""
        query = """
            SELECT 1 FROM invitation_acceptances
            WHERE invitation_id = %s AND user_id = %s
        """
        result = execute_query(query, (invitation_id, user_id), fetch_one=True)
        return result is not None

    def get_active_invitations_for_group(
        self, group_id: str
    ) -> list[dict]:
        """Get all active (not fully used/expired) invitations for a group."""
        query = """
            SELECT gi.id, gi.token, gi.created_at, gi.expires_at,
                   gi.max_uses, gi.current_uses,
                   p.name as created_by_name
            FROM group_invitations gi
            JOIN profiles p ON gi.invited_by = p.id
            WHERE gi.group_id = %s
              AND (gi.max_uses IS NULL OR gi.current_uses < gi.max_uses)
              AND (gi.expires_at IS NULL OR gi.expires_at > NOW())
            ORDER BY gi.created_at DESC
        """
        return execute_query(query, (group_id,))

    def get_invitation_acceptances(
        self, invitation_id: str
    ) -> list[InvitationAcceptanceEntity]:
        """Get list of users who accepted this invitation."""
        query = """
            SELECT ia.user_id, p.name as user_name, ia.accepted_at
            FROM invitation_acceptances ia
            JOIN profiles p ON ia.user_id = p.id
            WHERE ia.invitation_id = %s
            ORDER BY ia.accepted_at DESC
        """
        results = execute_query(query, (invitation_id,))
        return [InvitationAcceptanceEntity(**row) for row in results]

    def revoke_invitation(self, token: str) -> int:
        """Revoke an invitation by deleting it. Returns number of rows deleted."""
        return execute_delete("DELETE FROM group_invitations WHERE token = %s", (token,))
