"""Invitations service - business logic for group invitations."""

import os
import secrets
from datetime import UTC, datetime

from common.logger import setup_logger
from common.models import (
    InvitationAcceptResponse,
    InvitationCreateResponse,
    InvitationResponse,
    InviterInfo,
)
from repositories.invitations_repository import InvitationsRepository

from services.groups_service import BadRequestError, ForbiddenError, NotFoundError

logger = setup_logger(__name__)


class ConflictError(Exception):
    """Conflict error (resource already exists)."""

    pass


class GoneError(Exception):
    """Resource no longer available."""

    pass


class InvitationsService:
    """Service for invitations business logic."""

    def __init__(self, repository: InvitationsRepository | None = None):
        """Initialize service with repository."""
        self.repo = repository or InvitationsRepository()

    def create_invitation(
        self,
        user_id: str,
        group_id: str,
        role: str = "member",
        max_uses: int | None = None,
        expires_in_days: int | None = None,
    ) -> InvitationCreateResponse:
        """Create a multi-use group invitation (shareable link)."""
        # Verify user is admin of the group
        group_details = self.repo.get_group_details_for_user(user_id, group_id)
        if not group_details:
            raise ForbiddenError("You are not a member of this group")

        if group_details.user_role != "admin":
            raise ForbiddenError("Only group admins can invite members")

        # Generate unique token
        token = secrets.token_urlsafe(32)

        # Calculate expiration if specified
        expires_at = None
        if expires_in_days is not None:
            from datetime import timedelta
            expires_at = datetime.now(UTC) + timedelta(days=expires_in_days)

        # Create multi-use invitation
        invitation = self.repo.create_invitation(
            group_id=group_id,
            invited_by=user_id,
            role=role,
            token=token,
            max_uses=max_uses,
            expires_at=expires_at,
        )
        if not invitation:
            raise BadRequestError("Failed to create invitation")

        # Build invitation URL
        frontend_url = os.environ.get("FRONTEND_URL", "https://presently.com")
        invite_url = f"{frontend_url}/invite/{token}"

        return InvitationCreateResponse(
            invite_url=invite_url,
            max_uses=max_uses,
            current_uses=0,
            expires_at=expires_at,
        )

    def get_invitation(self, token: str) -> InvitationResponse:
        """Get invitation details (public endpoint)."""
        invitation = self.repo.get_invitation_by_token(token)

        if not invitation:
            raise NotFoundError("Invitation not found")

        # Get full invitation details to check status
        # Pass a placeholder UUID since this is a public endpoint (no authenticated user)
        invitation_details = self.repo.get_invitation_for_accept(None, token)

        # Check status but don't reject (all invitations are multi-use)
        is_expired = False
        is_full = False

        if invitation_details:
            if invitation_details.expires_at and invitation_details.expires_at < datetime.now(UTC):
                is_expired = True

            if invitation_details.max_uses and invitation_details.current_uses >= invitation_details.max_uses:
                is_full = True

        return InvitationResponse(
            group_id=invitation.group_id,
            group_name=invitation.group_name,
            group_description=invitation.group_description,
            invited_by=InviterInfo(
                name=invitation.inviter_name, email=invitation.inviter_email
            ),
            role=invitation.role,
            expires_at=invitation.expires_at,
            max_uses=invitation_details.max_uses if invitation_details else None,
            current_uses=invitation_details.current_uses if invitation_details else 0,
            is_expired=is_expired,
            is_full=is_full,
        )

    def accept_invitation(self, user_id: str, token: str) -> InvitationAcceptResponse:
        """Accept a group invitation (all invitations are multi-use)."""
        # Get invitation details
        invitation = self.repo.get_invitation_for_accept(user_id, token)

        if not invitation:
            raise NotFoundError("Invitation not found")

        # Check if expired
        if invitation.expires_at and invitation.expires_at < datetime.now(UTC):
            raise GoneError("This invitation has expired")

        # Check if max uses reached
        if invitation.max_uses and invitation.current_uses >= invitation.max_uses:
            raise GoneError("This invitation has reached its maximum uses")

        # Get invitation ID
        invitation_id = self.repo.get_invitation_id_by_token(token)
        if not invitation_id:
            raise NotFoundError("Invitation not found")

        # Check if this specific user already accepted this invitation
        if self.repo.has_user_accepted_invitation(str(invitation_id), user_id):
            # User already used this link - just return success
            return InvitationAcceptResponse(group_id=invitation.group_id, already_member=True)

        # Check if user is already a member (through different invitation)
        group_id = str(invitation.group_id)
        if self.repo.is_user_group_member(user_id, group_id):
            # Record acceptance anyway for tracking
            self.repo.record_invitation_acceptance(str(invitation_id), user_id)
            return InvitationAcceptResponse(group_id=invitation.group_id, already_member=True)

        # Add user to group
        membership_id = self.repo.add_user_to_group(user_id, group_id, invitation.role)
        if not membership_id:
            raise BadRequestError("Failed to add user to group")

        # Record acceptance and increment counter
        self.repo.record_invitation_acceptance(str(invitation_id), user_id)
        self.repo.increment_invitation_uses(token)

        return InvitationAcceptResponse(group_id=invitation.group_id, already_member=False)

    def get_active_invitations(self, user_id: str, group_id: str) -> list[dict]:
        """Get list of active multi-use invitations for a group (admin only)."""
        # Check if user is admin
        user_role = self.repo.get_user_role_in_group(user_id, group_id)

        if not user_role:
            raise ForbiddenError("You are not a member of this group")

        if user_role != "admin":
            raise ForbiddenError("Only group admins can view invitations")

        # Get active invitations
        invitations = self.repo.get_active_invitations_for_group(group_id)

        # For each invitation, get list of users who accepted
        frontend_url = os.environ.get("FRONTEND_URL", "https://presently.com")
        result = []
        for inv in invitations:
            acceptances = self.repo.get_invitation_acceptances(str(inv["id"]))
            result.append({
                "token": inv["token"],
                "invite_url": f"{frontend_url}/invite/{inv['token']}",
                "created_by": inv["created_by_name"],
                "created_at": inv["created_at"],
                "expires_at": inv["expires_at"],
                "max_uses": inv["max_uses"],
                "current_uses": inv["current_uses"],
                "accepted_by": [
                    {
                        "name": acc.user_name,
                        "accepted_at": acc.accepted_at,
                    }
                    for acc in acceptances
                ],
            })

        return result

    def revoke_invitation(self, user_id: str, token: str) -> None:
        """Revoke an invitation (admin only)."""
        # First get the invitation to check group membership
        invitation = self.repo.get_invitation_by_token(token)

        if not invitation:
            raise NotFoundError("Invitation not found")

        # Check if user is admin of the group
        user_role = self.repo.get_user_role_in_group(user_id, str(invitation.group_id))

        if not user_role:
            raise ForbiddenError("You are not a member of this group")

        if user_role != "admin":
            raise ForbiddenError("Only group admins can revoke invitations")

        # Delete the invitation
        rows_deleted = self.repo.revoke_invitation(token)

        if rows_deleted == 0:
            raise NotFoundError("Invitation not found")

    def remove_member(self, user_id: str, group_id: str, member_id: str) -> None:
        """Remove a member from a group (admin only)."""
        # Check if user is admin
        user_role = self.repo.get_user_role_in_group(user_id, group_id)

        if not user_role:
            raise ForbiddenError("You are not a member of this group")

        if user_role != "admin":
            raise ForbiddenError("Only group admins can remove members")

        # Prevent removing yourself (last admin could lock themselves out)
        if user_id == member_id:
            raise ForbiddenError("You cannot remove yourself from the group")

        # Delete membership
        rows_deleted = self.repo.remove_user_from_group(member_id, group_id)

        if rows_deleted == 0:
            raise NotFoundError("Member not found in this group")
