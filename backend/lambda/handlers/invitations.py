"""Group invitations Lambda handler."""

import secrets
from typing import Any

from common.auth import require_auth
from common.db import execute_insert, execute_query, execute_update
from common.models import (
    InvitationAcceptResponse,
    InvitationCreate,
    InvitationResponse,
    InviterInfo,
)
from common.responses import conflict, created, error, forbidden, not_found, success
from common.validators import get_path_parameter, validate_request_body


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Handle /invitations/* and /groups/{groupId}/members endpoints."""
    http_method = event["httpMethod"]
    path = event["path"]

    # Public endpoints (no auth required)
    if http_method == "GET" and "/invitations/" in path:
        token, param_error = get_path_parameter(event, "token")
        if param_error:
            return param_error
        return get_invitation(token)

    if http_method == "POST" and path.endswith("/accept"):
        token, param_error = get_path_parameter(event, "token")
        if param_error:
            return param_error
        # This endpoint requires auth
        user, auth_error = require_auth(event)
        if not user:
            return auth_error
        return accept_invitation(str(user.sub), token)

    # Auth required for other endpoints
    user, auth_error = require_auth(event)
    if not user:
        return auth_error

    user_id = str(user.sub)

    # Create invitation (send to group member)
    if http_method == "POST" and "/members" in path:
        group_id, param_error = get_path_parameter(event, "groupId", is_uuid=True)
        if param_error:
            return param_error
        return create_invitation(event, user_id, str(group_id))

    # Remove member from group
    if http_method == "DELETE" and "/members/" in path:
        group_id, param_error = get_path_parameter(event, "groupId", is_uuid=True)
        if param_error:
            return param_error
        member_id, param_error = get_path_parameter(event, "memberId", is_uuid=True)
        if param_error:
            return param_error
        return remove_member(user_id, str(group_id), str(member_id))

    return error("Not Found", 404)


def create_invitation(event: dict[str, Any], user_id: str, group_id: str) -> dict[str, Any]:
    """Create a group invitation."""
    # Validate request body
    invite_data, validation_error = validate_request_body(event, InvitationCreate)
    if validation_error:
        return validation_error

    # Check if user is admin of the group
    admin_query = """
        SELECT role FROM group_memberships
        WHERE user_id = %s AND group_id = %s
    """
    membership = execute_query(admin_query, (user_id, group_id), fetch_one=True)

    if not membership:
        return forbidden("You are not a member of this group")

    if membership["role"] != "admin":
        return forbidden("Only group admins can invite members")

    # Check if invitee is already a member
    existing_member_query = """
        SELECT 1 FROM group_memberships gm
        JOIN profiles p ON gm.user_id = p.id
        WHERE gm.group_id = %s AND p.email = %s
    """
    existing_member = execute_query(
        existing_member_query, (group_id, invite_data.email), fetch_one=True
    )

    if existing_member:
        return conflict("User is already a member of this group")

    # Check if there's already a pending invitation
    existing_invite_query = """
        SELECT id FROM group_invitations
        WHERE group_id = %s AND email = %s AND accepted_at IS NULL
    """
    existing_invite = execute_query(
        existing_invite_query, (group_id, invite_data.email), fetch_one=True
    )

    if existing_invite:
        return conflict("An invitation has already been sent to this email")

    # Generate unique token
    token = secrets.token_urlsafe(32)

    # Create invitation
    invitation_query = """
        INSERT INTO group_invitations (group_id, invited_by, email, role, token)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id, token
    """

    result = execute_insert(
        invitation_query, (group_id, user_id, invite_data.email, invite_data.role, token)
    )

    if not result:
        return error("Failed to create invitation", 500)

    # TODO: Send email with invitation link
    # For now, just return the token
    invite_url = f"https://presently.com/invite/{token}"

    return created({"added_directly": False, "invite_url": invite_url, "email_sent": False})


def get_invitation(token: str) -> dict[str, Any]:
    """Get invitation details (public endpoint)."""
    query = """
        SELECT gi.group_id, g.name as group_name, g.description as group_description,
               gi.role, gi.expires_at, gi.accepted_at,
               p.name as inviter_name, p.email as inviter_email
        FROM group_invitations gi
        JOIN groups g ON gi.group_id = g.id
        JOIN profiles p ON gi.invited_by = p.id
        WHERE gi.token = %s
    """

    result = execute_query(query, (token,), fetch_one=True)

    if not result:
        return not_found("Invitation not found")

    # Check if already accepted
    if result["accepted_at"]:
        return error("This invitation has already been accepted", 410)

    # Check if expired
    from datetime import datetime, timezone

    if result["expires_at"] < datetime.now(timezone.utc):
        return error("This invitation has expired", 410)

    invitation = InvitationResponse(
        group_id=result["group_id"],
        group_name=result["group_name"],
        group_description=result["group_description"],
        invited_by=InviterInfo(name=result["inviter_name"], email=result["inviter_email"]),
        role=result["role"],
        expires_at=result["expires_at"],
    )

    return success(invitation)


def accept_invitation(user_id: str, token: str) -> dict[str, Any]:
    """Accept a group invitation."""
    # Get invitation details
    invitation_query = """
        SELECT gi.group_id, gi.email, gi.role, gi.accepted_at, gi.expires_at,
               p.email as user_email
        FROM group_invitations gi
        LEFT JOIN profiles p ON p.id = %s
        WHERE gi.token = %s
    """

    invitation = execute_query(invitation_query, (user_id, token), fetch_one=True)

    if not invitation:
        return not_found("Invitation not found")

    # Check if already accepted
    if invitation["accepted_at"]:
        return error("This invitation has already been accepted", 410)

    # Check if expired
    from datetime import datetime, timezone

    if invitation["expires_at"] < datetime.now(timezone.utc):
        return error("This invitation has expired", 410)

    # Verify email matches (if user has email in profile)
    if invitation["user_email"] and invitation["user_email"] != invitation["email"]:
        return forbidden("This invitation was sent to a different email address")

    group_id = invitation["group_id"]
    role = invitation["role"]

    # Check if user is already a member
    existing_member_query = """
        SELECT 1 FROM group_memberships
        WHERE user_id = %s AND group_id = %s
    """
    existing_member = execute_query(existing_member_query, (user_id, group_id), fetch_one=True)

    if existing_member:
        # Mark invitation as accepted anyway
        execute_update(
            "UPDATE group_invitations SET accepted_at = NOW() WHERE token = %s", (token,)
        )
        return success(InvitationAcceptResponse(group_id=group_id, already_member=True))

    # Add user to group
    membership_query = """
        INSERT INTO group_memberships (user_id, group_id, role)
        VALUES (%s, %s, %s)
    """

    execute_insert(membership_query, (user_id, group_id, role))

    # Mark invitation as accepted
    execute_update("UPDATE group_invitations SET accepted_at = NOW() WHERE token = %s", (token,))

    return success(InvitationAcceptResponse(group_id=group_id, already_member=False))


def remove_member(user_id: str, group_id: str, member_id: str) -> dict[str, Any]:
    """Remove a member from a group (admin only)."""
    # Check if user is admin
    admin_query = """
        SELECT role FROM group_memberships
        WHERE user_id = %s AND group_id = %s
    """
    membership = execute_query(admin_query, (user_id, group_id), fetch_one=True)

    if not membership:
        return forbidden("You are not a member of this group")

    if membership["role"] != "admin":
        return forbidden("Only group admins can remove members")

    # Prevent removing yourself (last admin could lock themselves out)
    if user_id == member_id:
        return forbidden("You cannot remove yourself from the group")

    # Delete membership
    from common.responses import no_content

    delete_query = """
        DELETE FROM group_memberships
        WHERE user_id = %s AND group_id = %s
    """

    from common.db import execute_delete

    rows_deleted = execute_delete(delete_query, (member_id, group_id))

    if rows_deleted == 0:
        return not_found("Member not found in this group")

    return no_content()
