"""Group invitations router."""

import os
import secrets
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from common.db import execute_delete, execute_insert, execute_query, execute_update
from common.email_templates import get_existing_user_email, get_new_user_email
from common.emails import send_email
from common.models import (
    AuthenticatedUser,
    InvitationAcceptResponse,
    InvitationCreate,
    InvitationResponse,
    InviterInfo,
)
from dependencies.auth import get_current_user

router = APIRouter()


@router.post("/groups/{group_id}/members", status_code=status.HTTP_201_CREATED)
async def create_invitation(
    group_id: UUID,
    invite_data: InvitationCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Create a group invitation."""
    user_id = str(current_user.sub)

    # Check if user is admin of the group and get group details
    group_query = """
        SELECT g.name, g.description, gm.role
        FROM groups g
        JOIN group_memberships gm ON g.id = gm.group_id
        WHERE gm.user_id = %s AND gm.group_id = %s
    """
    group_result = execute_query(group_query, (user_id, str(group_id)), fetch_one=True)

    if not group_result:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this group",
        )

    if group_result["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only group admins can invite members",
        )

    group_name = group_result["name"]
    group_description = group_result["description"]

    # Check if invitee is already a member
    existing_member_query = """
        SELECT 1 FROM group_memberships gm
        JOIN profiles p ON gm.user_id = p.id
        WHERE gm.group_id = %s AND p.email = %s
    """
    existing_member = execute_query(
        existing_member_query, (str(group_id), invite_data.email), fetch_one=True
    )

    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a member of this group",
        )

    # Check if there's already a pending invitation
    existing_invite_query = """
        SELECT id FROM group_invitations
        WHERE group_id = %s AND email = %s AND accepted_at IS NULL
    """
    existing_invite = execute_query(
        existing_invite_query, (str(group_id), invite_data.email), fetch_one=True
    )

    if existing_invite:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An invitation has already been sent to this email",
        )

    # Check if user exists in the system (has a profile)
    user_exists_query = "SELECT id, name, email FROM profiles WHERE email = %s"
    existing_user = execute_query(user_exists_query, (invite_data.email,), fetch_one=True)
    user_exists = existing_user is not None

    # Get inviter info for email
    inviter_query = "SELECT name, email FROM profiles WHERE id = %s"
    inviter = execute_query(inviter_query, (user_id,), fetch_one=True)
    inviter_name = inviter["name"] if inviter else "Someone"
    inviter_email = inviter["email"] if inviter else ""

    # Generate unique token
    token = secrets.token_urlsafe(32)

    # Create invitation
    invitation_query = """
        INSERT INTO group_invitations (group_id, invited_by, email, role, token)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id, token
    """

    result = execute_insert(
        invitation_query, (str(group_id), user_id, invite_data.email, invite_data.role, token)
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create invitation",
        )

    # Build invitation URL
    frontend_url = os.environ.get("FRONTEND_URL", "https://presently.com")
    invite_url = f"{frontend_url}/invite/{token}"

    # Send appropriate email based on whether user exists
    email_sent = False

    if user_exists:
        # User already has account - send "join group" email
        subject, html_body, text_body = get_existing_user_email(
            inviter_name=inviter_name,
            group_name=group_name,
            group_description=group_description,
            invite_url=invite_url,
        )
        email_sent = send_email(invite_data.email, subject, html_body, text_body)
    else:
        # New user - send "register and join" email
        subject, html_body, text_body = get_new_user_email(
            inviter_name=inviter_name,
            inviter_email=inviter_email,
            group_name=group_name,
            group_description=group_description,
            invite_url=invite_url,
        )
        email_sent = send_email(invite_data.email, subject, html_body, text_body)

    return {
        "added_directly": False,
        "invite_url": invite_url,
        "email_sent": email_sent,
        "user_exists": user_exists,
    }


@router.get("/invitations/{token}", response_model=InvitationResponse)
async def get_invitation(token: str):
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found",
        )

    # Check if already accepted
    if result["accepted_at"]:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This invitation has already been accepted",
        )

    # Check if expired
    if result["expires_at"] < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This invitation has expired",
        )

    invitation = InvitationResponse(
        group_id=result["group_id"],
        group_name=result["group_name"],
        group_description=result["group_description"],
        invited_by=InviterInfo(name=result["inviter_name"], email=result["inviter_email"]),
        role=result["role"],
        expires_at=result["expires_at"],
    )

    return invitation


@router.post("/invitations/{token}/accept", response_model=InvitationAcceptResponse)
async def accept_invitation(
    token: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Accept a group invitation."""
    user_id = str(current_user.sub)

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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found",
        )

    # Check if already accepted
    if invitation["accepted_at"]:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This invitation has already been accepted",
        )

    # Check if expired
    if invitation["expires_at"] < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This invitation has expired",
        )

    # Verify email matches (if user has email in profile)
    if invitation["user_email"] and invitation["user_email"] != invitation["email"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This invitation was sent to a different email address",
        )

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
        return InvitationAcceptResponse(group_id=group_id, already_member=True)

    # Add user to group
    membership_query = """
        INSERT INTO group_memberships (user_id, group_id, role)
        VALUES (%s, %s, %s)
        RETURNING id
    """

    result = execute_insert(membership_query, (user_id, group_id, role))

    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add user to group",
        )

    # Mark invitation as accepted
    execute_update("UPDATE group_invitations SET accepted_at = NOW() WHERE token = %s", (token,))

    return InvitationAcceptResponse(group_id=group_id, already_member=False)


@router.delete("/groups/{group_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    group_id: UUID,
    member_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    """Remove a member from a group (admin only)."""
    user_id = str(current_user.sub)

    # Check if user is admin
    admin_query = """
        SELECT role FROM group_memberships
        WHERE user_id = %s AND group_id = %s
    """
    membership = execute_query(admin_query, (user_id, str(group_id)), fetch_one=True)

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this group",
        )

    if membership["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only group admins can remove members",
        )

    # Prevent removing yourself (last admin could lock themselves out)
    if user_id == str(member_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot remove yourself from the group",
        )

    # Delete membership
    delete_query = """
        DELETE FROM group_memberships
        WHERE user_id = %s AND group_id = %s
    """

    rows_deleted = execute_delete(delete_query, (str(member_id), str(group_id)))

    if rows_deleted == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found in this group",
        )
