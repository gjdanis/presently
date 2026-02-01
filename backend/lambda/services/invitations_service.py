"""Invitations service - business logic for group invitations."""

import os
import secrets
from datetime import UTC, datetime

from common.email_templates import get_existing_user_email, get_new_user_email
from common.emails import send_email
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
        self, user_id: str, group_id: str, email: str, role: str = "member"
    ) -> InvitationCreateResponse:
        """Create a group invitation and send email."""
        # Verify user is admin of the group
        group_details = self.repo.get_group_details_for_user(user_id, group_id)
        if not group_details:
            raise ForbiddenError("You are not a member of this group")

        if group_details.user_role != "admin":
            raise ForbiddenError("Only group admins can invite members")

        # Check if invitee is already a member
        if self.repo.is_user_already_member(group_id, email):
            raise ConflictError("User is already a member of this group")

        # Check if there's already a pending invitation
        if self.repo.has_pending_invitation(group_id, email):
            raise ConflictError("An invitation has already been sent to this email")

        # Check if user exists in the system
        existing_user = self.repo.get_user_by_email(email)
        user_exists = existing_user is not None

        # Get inviter info for email
        inviter = self.repo.get_user_profile(user_id)
        inviter_name = inviter.name if inviter else "Someone"
        inviter_email = inviter.email if inviter else ""

        # Generate unique token
        token = secrets.token_urlsafe(32)

        # Create invitation
        invitation = self.repo.create_invitation(group_id, user_id, email, role, token)
        if not invitation:
            raise BadRequestError("Failed to create invitation")

        # Build invitation URL
        frontend_url = os.environ.get("FRONTEND_URL", "https://presently.com")
        invite_url = f"{frontend_url}/invite/{token}"

        # Send appropriate email based on whether user exists
        email_sent = False

        if user_exists:
            # User already has account - send "join group" email
            subject, html_body, text_body = get_existing_user_email(
                inviter_name=inviter_name,
                group_name=group_details.name,
                group_description=group_details.description,
                invite_url=invite_url,
            )
            email_sent = send_email(email, subject, html_body, text_body)
        else:
            # New user - send "register and join" email
            subject, html_body, text_body = get_new_user_email(
                inviter_name=inviter_name,
                inviter_email=inviter_email,
                group_name=group_details.name,
                group_description=group_details.description,
                invite_url=invite_url,
            )
            email_sent = send_email(email, subject, html_body, text_body)

        return InvitationCreateResponse(
            added_directly=False,
            invite_url=invite_url,
            email_sent=email_sent,
            user_exists=user_exists,
        )

    def get_invitation(self, token: str) -> InvitationResponse:
        """Get invitation details (public endpoint)."""
        invitation = self.repo.get_invitation_by_token(token)

        if not invitation:
            raise NotFoundError("Invitation not found")

        # Check if already accepted
        if invitation.accepted_at:
            raise GoneError("This invitation has already been accepted")

        # Check if expired
        if invitation.expires_at < datetime.now(UTC):
            raise GoneError("This invitation has expired")

        return InvitationResponse(
            group_id=invitation.group_id,
            group_name=invitation.group_name,
            group_description=invitation.group_description,
            invited_by=InviterInfo(
                name=invitation.inviter_name, email=invitation.inviter_email
            ),
            role=invitation.role,
            expires_at=invitation.expires_at,
        )

    def accept_invitation(self, user_id: str, token: str) -> InvitationAcceptResponse:
        """Accept a group invitation."""
        # Get invitation details
        invitation = self.repo.get_invitation_for_accept(user_id, token)

        if not invitation:
            raise NotFoundError("Invitation not found")

        # Check if already accepted
        if invitation.accepted_at:
            raise GoneError("This invitation has already been accepted")

        # Check if expired
        if invitation.expires_at < datetime.now(UTC):
            raise GoneError("This invitation has expired")

        # Verify email matches (if user has email in profile)
        if invitation.user_email and invitation.user_email != invitation.email:
            raise ForbiddenError("This invitation was sent to a different email address")

        group_id = str(invitation.group_id)
        role = invitation.role

        # Check if user is already a member
        if self.repo.is_user_group_member(user_id, group_id):
            # Mark invitation as accepted anyway
            self.repo.mark_invitation_accepted(token)
            return InvitationAcceptResponse(group_id=invitation.group_id, already_member=True)

        # Add user to group
        membership_id = self.repo.add_user_to_group(user_id, group_id, role)
        if not membership_id:
            raise BadRequestError("Failed to add user to group")

        # Mark invitation as accepted
        self.repo.mark_invitation_accepted(token)

        return InvitationAcceptResponse(group_id=invitation.group_id, already_member=False)

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
