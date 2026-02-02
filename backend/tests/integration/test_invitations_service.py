"""Integration tests for InvitationsService."""

from typing import Any
from uuid import UUID, uuid4

import pytest
from services.groups_service import ForbiddenError, NotFoundError
from services.invitations_service import ConflictError, GoneError, InvitationsService


@pytest.fixture
def invitations_service() -> InvitationsService:
    """Create an InvitationsService instance."""
    return InvitationsService()


def test_create_multi_use_invitation_basic(
    clean_db: Any,
    sample_profile: dict[str, Any],
    sample_group: dict[str, Any],
    invitations_service: InvitationsService,
):
    """Test creating a basic multi-use invitation with no limits."""
    result = invitations_service.create_invitation(
        user_id=sample_profile["id"],
        group_id=sample_group["id"],
        role="member",
    )

    assert result.added_directly is False
    assert result.email_sent is False
    assert result.user_exists is False
    assert result.invite_url.startswith("https://")
    assert "/invite/" in result.invite_url
    assert result.max_uses is None  # Unlimited
    assert result.current_uses == 0
    assert result.expires_at is None  # Never expires


def test_create_multi_use_invitation_with_limits(
    clean_db: Any,
    sample_profile: dict[str, Any],
    sample_group: dict[str, Any],
    invitations_service: InvitationsService,
):
    """Test creating a multi-use invitation with usage limits and expiration."""
    result = invitations_service.create_invitation(
        user_id=sample_profile["id"],
        group_id=sample_group["id"],
        role="member",
        max_uses=5,
        expires_in_days=7,
    )

    assert result.max_uses == 5
    assert result.current_uses == 0
    assert result.expires_at is not None


def test_create_invitation_non_admin(
    clean_db: Any,
    sample_profile: dict[str, Any],
    sample_group: dict[str, Any],
    invitations_service: InvitationsService,
):
    """Test that non-admin users cannot create invitations."""
    # Create a second user who is a member but not admin
    from repositories.profile_repository import ProfileRepository
    from repositories.invitations_repository import InvitationsRepository

    profiles_repo = ProfileRepository()
    invitations_repo = InvitationsRepository()

    member_profile = profiles_repo.create_profile(
        user_id=str(uuid4()),
        email="member@example.com",
        name="Member User",
    )

    # Add as member (not admin)
    invitations_repo.add_user_to_group(str(member_profile.id), sample_group["id"], "member")

    # Try to create invitation as non-admin
    with pytest.raises(ForbiddenError, match="Only group admins"):
        invitations_service.create_invitation(
            user_id=str(member_profile.id),
            group_id=sample_group["id"],
            role="member",
        )


def test_get_invitation(
    clean_db: Any,
    sample_profile: dict[str, Any],
    sample_group: dict[str, Any],
    invitations_service: InvitationsService,
):
    """Test getting invitation details."""
    # Create invitation
    result = invitations_service.create_invitation(
        user_id=sample_profile["id"],
        group_id=sample_group["id"],
        role="member",
        max_uses=10,
    )

    # Extract token from URL
    token = result.invite_url.split("/invite/")[-1]

    # Get invitation details
    invitation = invitations_service.get_invitation(token)

    assert str(invitation.group_id) == sample_group["id"]
    assert invitation.group_name == sample_group["name"]
    assert invitation.role == "member"
    assert invitation.max_uses == 10
    assert invitation.current_uses == 0
    assert invitation.is_expired is False
    assert invitation.is_full is False


def test_get_invitation_not_found(invitations_service: InvitationsService):
    """Test getting a non-existent invitation."""
    with pytest.raises(NotFoundError, match="Invitation not found"):
        invitations_service.get_invitation("invalid-token")


def test_accept_invitation(
    clean_db: Any,
    sample_profile: dict[str, Any],
    sample_group: dict[str, Any],
    invitations_service: InvitationsService,
):
    """Test accepting a multi-use invitation."""
    from repositories.profile_repository import ProfileRepository

    # Create invitation
    result = invitations_service.create_invitation(
        user_id=sample_profile["id"],
        group_id=sample_group["id"],
        role="member",
    )
    token = result.invite_url.split("/invite/")[-1]

    # Create a new user to accept the invitation
    profiles_repo = ProfileRepository()
    new_user = profiles_repo.create_profile(
        user_id=str(uuid4()),
        email="newuser@example.com",
        name="New User",
    )

    # Accept invitation
    accept_result = invitations_service.accept_invitation(str(new_user.id), token)

    assert str(accept_result.group_id) == sample_group["id"]
    assert accept_result.already_member is False

    # Verify user is now a member
    from services.groups_service import GroupsService

    groups_service = GroupsService()
    groups = groups_service.get_user_groups(str(new_user.id))
    assert len(groups) == 1
    assert str(groups[0].id) == sample_group["id"]
    assert groups[0].role == "member"


def test_accept_invitation_multiple_users(
    clean_db: Any,
    sample_profile: dict[str, Any],
    sample_group: dict[str, Any],
    invitations_service: InvitationsService,
):
    """Test multiple users accepting the same invitation."""
    from repositories.profile_repository import ProfileRepository

    # Create invitation
    result = invitations_service.create_invitation(
        user_id=sample_profile["id"],
        group_id=sample_group["id"],
        role="member",
        max_uses=3,
    )
    token = result.invite_url.split("/invite/")[-1]

    # Create three users
    profiles_repo = ProfileRepository()
    users = []
    for i in range(3):
        user = profiles_repo.create_profile(
            user_id=str(uuid4()),
            email=f"user{i}@example.com",
            name=f"User {i}",
        )
        users.append(user)

    # All three accept the invitation
    for user in users:
        accept_result = invitations_service.accept_invitation(str(user.id), token)
        assert accept_result.already_member is False

    # Check invitation usage count
    invitation = invitations_service.get_invitation(token)
    assert invitation.current_uses == 3
    assert invitation.is_full is True

    # Try to accept with a fourth user - should fail
    user4 = profiles_repo.create_profile(
        user_id=str(uuid4()),
        email="user4@example.com",
        name="User 4",
    )

    with pytest.raises(GoneError, match="maximum uses"):
        invitations_service.accept_invitation(str(user4.id), token)


def test_accept_invitation_already_used_by_same_user(
    clean_db: Any,
    sample_profile: dict[str, Any],
    sample_group: dict[str, Any],
    invitations_service: InvitationsService,
):
    """Test that the same user cannot accept the same invitation twice."""
    from repositories.profile_repository import ProfileRepository

    # Create invitation
    result = invitations_service.create_invitation(
        user_id=sample_profile["id"],
        group_id=sample_group["id"],
        role="member",
    )
    token = result.invite_url.split("/invite/")[-1]

    # Create user and accept
    profiles_repo = ProfileRepository()
    user = profiles_repo.create_profile(
        user_id=str(uuid4()),
        email="user@example.com",
        name="User",
    )

    # First acceptance
    result1 = invitations_service.accept_invitation(str(user.id), token)
    assert result1.already_member is False

    # Second acceptance by same user
    result2 = invitations_service.accept_invitation(str(user.id), token)
    assert result2.already_member is True  # Returns success but doesn't re-add


def test_accept_invitation_expired(
    clean_db: Any,
    sample_profile: dict[str, Any],
    sample_group: dict[str, Any],
    invitations_service: InvitationsService,
):
    """Test that expired invitations cannot be accepted."""
    from datetime import UTC, datetime, timedelta
    from repositories.invitations_repository import InvitationsRepository
    import secrets

    # Create an expired invitation directly in the database
    repo = InvitationsRepository()
    token = secrets.token_urlsafe(32)
    expired_time = datetime.now(UTC) - timedelta(days=1)

    repo.create_invitation(
        group_id=sample_group["id"],
        invited_by=sample_profile["id"],
        email=None,
        role="member",
        token=token,
        is_multi_use=True,
        max_uses=None,
        expires_at=expired_time,
    )

    # Try to accept
    from repositories.profile_repository import ProfileRepository

    profiles_repo = ProfileRepository()
    user = profiles_repo.create_profile(
        user_id=str(uuid4()),
        email="user@example.com",
        name="User",
    )

    with pytest.raises(GoneError, match="expired"):
        invitations_service.accept_invitation(str(user.id), token)


def test_get_active_invitations(
    clean_db: Any,
    sample_profile: dict[str, Any],
    sample_group: dict[str, Any],
    invitations_service: InvitationsService,
):
    """Test getting list of active invitations."""
    # Create multiple invitations
    invitations_service.create_invitation(
        user_id=sample_profile["id"],
        group_id=sample_group["id"],
        role="member",
        max_uses=5,
    )

    invitations_service.create_invitation(
        user_id=sample_profile["id"],
        group_id=sample_group["id"],
        role="member",
        max_uses=10,
        expires_in_days=7,
    )

    # Get active invitations
    active = invitations_service.get_active_invitations(
        sample_profile["id"], sample_group["id"]
    )

    assert len(active) == 2
    assert active[0]["max_uses"] in [5, 10]
    assert active[0]["current_uses"] == 0
    assert "invite_url" in active[0]
    assert "created_by" in active[0]
    assert "accepted_by" in active[0]


def test_get_active_invitations_non_admin(
    clean_db: Any,
    sample_profile: dict[str, Any],
    sample_group: dict[str, Any],
    invitations_service: InvitationsService,
):
    """Test that non-admin users cannot view active invitations."""
    from repositories.profile_repository import ProfileRepository
    from repositories.invitations_repository import InvitationsRepository

    profiles_repo = ProfileRepository()
    invitations_repo = InvitationsRepository()

    member_profile = profiles_repo.create_profile(
        user_id=str(uuid4()),
        email="member@example.com",
        name="Member User",
    )

    invitations_repo.add_user_to_group(str(member_profile.id), sample_group["id"], "member")

    with pytest.raises(ForbiddenError, match="Only group admins"):
        invitations_service.get_active_invitations(
            str(member_profile.id), sample_group["id"]
        )


def test_revoke_invitation(
    clean_db: Any,
    sample_profile: dict[str, Any],
    sample_group: dict[str, Any],
    invitations_service: InvitationsService,
):
    """Test revoking an invitation."""
    # Create invitation
    result = invitations_service.create_invitation(
        user_id=sample_profile["id"],
        group_id=sample_group["id"],
        role="member",
    )
    token = result.invite_url.split("/invite/")[-1]

    # Verify it exists
    invitation = invitations_service.get_invitation(token)
    assert invitation is not None

    # Revoke it
    invitations_service.revoke_invitation(sample_profile["id"], token)

    # Verify it's gone
    with pytest.raises(NotFoundError):
        invitations_service.get_invitation(token)


def test_revoke_invitation_non_admin(
    clean_db: Any,
    sample_profile: dict[str, Any],
    sample_group: dict[str, Any],
    invitations_service: InvitationsService,
):
    """Test that non-admin users cannot revoke invitations."""
    from repositories.profile_repository import ProfileRepository
    from repositories.invitations_repository import InvitationsRepository

    # Create invitation as admin
    result = invitations_service.create_invitation(
        user_id=sample_profile["id"],
        group_id=sample_group["id"],
        role="member",
    )
    token = result.invite_url.split("/invite/")[-1]

    # Create non-admin member
    profiles_repo = ProfileRepository()
    invitations_repo = InvitationsRepository()

    member_profile = profiles_repo.create_profile(
        user_id=str(uuid4()),
        email="member@example.com",
        name="Member User",
    )

    invitations_repo.add_user_to_group(str(member_profile.id), sample_group["id"], "member")

    # Try to revoke as non-admin
    with pytest.raises(ForbiddenError, match="Only group admins"):
        invitations_service.revoke_invitation(str(member_profile.id), token)


def test_remove_member(
    clean_db: Any,
    sample_profile: dict[str, Any],
    sample_group: dict[str, Any],
    invitations_service: InvitationsService,
):
    """Test removing a member from a group."""
    from repositories.profile_repository import ProfileRepository
    from repositories.invitations_repository import InvitationsRepository

    profiles_repo = ProfileRepository()
    invitations_repo = InvitationsRepository()

    # Add a member to the group
    member_profile = profiles_repo.create_profile(
        user_id=str(uuid4()),
        email="member@example.com",
        name="Member User",
    )

    invitations_repo.add_user_to_group(str(member_profile.id), sample_group["id"], "member")

    # Verify member is in group
    from services.groups_service import GroupsService

    groups_service = GroupsService()
    detail = groups_service.get_group_detail(sample_profile["id"], sample_group["id"])
    assert len(detail.members) == 2

    # Remove member
    invitations_service.remove_member(
        sample_profile["id"], sample_group["id"], str(member_profile.id)
    )

    # Verify member is gone
    detail = groups_service.get_group_detail(sample_profile["id"], sample_group["id"])
    assert len(detail.members) == 1


def test_remove_member_non_admin(
    clean_db: Any,
    sample_profile: dict[str, Any],
    sample_group: dict[str, Any],
    invitations_service: InvitationsService,
):
    """Test that non-admin users cannot remove members."""
    from repositories.profile_repository import ProfileRepository
    from repositories.invitations_repository import InvitationsRepository

    profiles_repo = ProfileRepository()
    invitations_repo = InvitationsRepository()

    # Create two members
    member1 = profiles_repo.create_profile(
        user_id=str(uuid4()),
        email="member1@example.com",
        name="Member 1",
    )

    member2 = profiles_repo.create_profile(
        user_id=str(uuid4()),
        email="member2@example.com",
        name="Member 2",
    )

    invitations_repo.add_user_to_group(str(member1.id), sample_group["id"], "member")
    invitations_repo.add_user_to_group(str(member2.id), sample_group["id"], "member")

    # Try to remove member2 as member1 (non-admin)
    with pytest.raises(ForbiddenError, match="Only group admins"):
        invitations_service.remove_member(
            str(member1.id), sample_group["id"], str(member2.id)
        )


def test_remove_self(
    clean_db: Any,
    sample_profile: dict[str, Any],
    sample_group: dict[str, Any],
    invitations_service: InvitationsService,
):
    """Test that users cannot remove themselves."""
    with pytest.raises(ForbiddenError, match="cannot remove yourself"):
        invitations_service.remove_member(
            sample_profile["id"], sample_group["id"], sample_profile["id"]
        )
