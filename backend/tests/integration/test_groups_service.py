"""Integration tests for GroupsService."""

from typing import Any
from uuid import UUID

import pytest
from services.groups_service import (
    BadRequestError,
    ForbiddenError,
    GroupsService,
    NotFoundError,
)


@pytest.fixture
def groups_service() -> GroupsService:
    """Create a GroupsService instance."""
    return GroupsService()


def test_get_user_groups_empty(
    clean_db: Any, sample_profile: dict[str, Any], groups_service: GroupsService
):
    """Test getting groups for a user with no groups."""
    groups = groups_service.get_user_groups(sample_profile["id"])
    assert groups == []


def test_get_user_groups_with_data(
    clean_db: Any, sample_profile: dict[str, Any], sample_group: dict[str, Any], groups_service: GroupsService
):
    """Test getting groups for a user with groups."""
    groups = groups_service.get_user_groups(sample_profile["id"])
    assert len(groups) == 1
    assert str(groups[0].id) == sample_group["id"]
    assert groups[0].name == sample_group["name"]
    assert groups[0].role == "admin"
    assert groups[0].member_count == 1


def test_create_group(
    clean_db: Any, sample_profile: dict[str, Any], groups_service: GroupsService
):
    """Test creating a new group."""
    group = groups_service.create_group(
        user_id=sample_profile["id"],
        name="New Test Group",
        description="A new test group"
    )

    assert group.name == "New Test Group"
    assert group.description == "A new test group"
    assert group.id is not None

    # Verify user is admin
    groups = groups_service.get_user_groups(sample_profile["id"])
    assert len(groups) == 1
    assert groups[0].role == "admin"


def test_get_group_detail(
    clean_db: Any, sample_profile: dict[str, Any], sample_group: dict[str, Any], groups_service: GroupsService
):
    """Test getting group details."""
    detail = groups_service.get_group_detail(sample_profile["id"], sample_group["id"])

    assert str(detail.group.id) == sample_group["id"]
    assert detail.group.name == sample_group["name"]
    assert len(detail.members) == 1
    assert str(detail.members[0].user_id) == sample_profile["id"]
    assert detail.members[0].role == "admin"
    # Should have wishlist for the one member (even if empty)
    assert len(detail.wishlists) == 1
    assert detail.wishlists[0].userId == sample_profile["id"]
    assert detail.wishlists[0].items == []


def test_get_group_detail_forbidden(
    clean_db: Any, sample_profile: dict[str, Any], sample_group: dict[str, Any], groups_service: GroupsService
):
    """Test getting group details for a group user is not a member of."""
    from uuid import uuid4

    non_member_id = str(uuid4())

    with pytest.raises(ForbiddenError, match="not a member"):
        groups_service.get_group_detail(non_member_id, sample_group["id"])


def test_update_group(
    clean_db: Any, sample_profile: dict[str, Any], sample_group: dict[str, Any], groups_service: GroupsService
):
    """Test updating a group."""
    updated = groups_service.update_group(
        user_id=sample_profile["id"],
        group_id=sample_group["id"],
        name="Updated Name",
        description="Updated description"
    )

    assert updated.name == "Updated Name"
    assert updated.description == "Updated description"


def test_update_group_not_admin(
    clean_db: Any, sample_profile: dict[str, Any], sample_group: dict[str, Any], groups_service: GroupsService
):
    """Test updating a group as non-admin."""
    from uuid import uuid4

    # Create another user
    cursor = clean_db.cursor()
    member_id = str(uuid4())
    cursor.execute(
        "INSERT INTO profiles (id, email, name) VALUES (%s, %s, %s)",
        (member_id, "member@example.com", "Member")
    )
    cursor.execute(
        "INSERT INTO group_memberships (user_id, group_id, role) VALUES (%s, %s, %s)",
        (member_id, sample_group["id"], "member")
    )
    clean_db.commit()
    cursor.close()

    with pytest.raises(ForbiddenError, match="Only group admins"):
        groups_service.update_group(
            user_id=member_id,
            group_id=sample_group["id"],
            name="Hacked Name",
            description=None
        )


def test_delete_group(
    clean_db: Any, sample_profile: dict[str, Any], sample_group: dict[str, Any], groups_service: GroupsService
):
    """Test deleting a group."""
    groups_service.delete_group(sample_profile["id"], sample_group["id"])

    # Verify group is deleted
    with pytest.raises(ForbiddenError):
        groups_service.get_group_detail(sample_profile["id"], sample_group["id"])


def test_delete_group_not_admin(
    clean_db: Any, sample_profile: dict[str, Any], sample_group: dict[str, Any], groups_service: GroupsService
):
    """Test deleting a group as non-admin."""
    from uuid import uuid4

    # Create another user
    cursor = clean_db.cursor()
    member_id = str(uuid4())
    cursor.execute(
        "INSERT INTO profiles (id, email, name) VALUES (%s, %s, %s)",
        (member_id, "member@example.com", "Member")
    )
    cursor.execute(
        "INSERT INTO group_memberships (user_id, group_id, role) VALUES (%s, %s, %s)",
        (member_id, sample_group["id"], "member")
    )
    clean_db.commit()
    cursor.close()

    with pytest.raises(ForbiddenError, match="Only group admins"):
        groups_service.delete_group(member_id, sample_group["id"])


def test_remove_member(
    clean_db: Any, sample_profile: dict[str, Any], sample_group: dict[str, Any], groups_service: GroupsService
):
    """Test removing a member from a group."""
    from uuid import uuid4

    # Create another user
    cursor = clean_db.cursor()
    member_id = str(uuid4())
    cursor.execute(
        "INSERT INTO profiles (id, email, name) VALUES (%s, %s, %s)",
        (member_id, "member@example.com", "Member")
    )
    cursor.execute(
        "INSERT INTO group_memberships (user_id, group_id, role) VALUES (%s, %s, %s)",
        (member_id, sample_group["id"], "member")
    )
    clean_db.commit()
    cursor.close()

    # Remove member
    groups_service.remove_member(sample_profile["id"], sample_group["id"], member_id)

    # Verify member is removed
    detail = groups_service.get_group_detail(sample_profile["id"], sample_group["id"])
    assert len(detail.members) == 1
    assert str(detail.members[0].user_id) == sample_profile["id"]


def test_remove_member_self(
    clean_db: Any, sample_profile: dict[str, Any], sample_group: dict[str, Any], groups_service: GroupsService
):
    """Test admin cannot remove themselves if they're the only admin."""
    with pytest.raises(BadRequestError, match="Cannot remove the only admin"):
        groups_service.remove_member(
            sample_profile["id"],
            sample_group["id"],
            sample_profile["id"]
        )
