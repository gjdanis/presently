"""Integration tests for groups endpoints with real database."""

import json
from typing import Any
from uuid import uuid4

from common.db import execute_query, execute_update


def test_create_group_and_membership(clean_db: Any, sample_profile: dict[str, Any]) -> None:
    """Test creating a group creates both group and membership."""
    from handlers.groups import create_group

    event = {
        "body": json.dumps({
            "name": "Integration Test Group",
            "description": "Testing group creation"
        })
    }

    response = create_group(event, sample_profile["id"])

    assert response["statusCode"] == 201

    body = json.loads(response["body"])
    assert body["name"] == "Integration Test Group"
    assert body["role"] == "admin"
    assert body["member_count"] == 1

    # Verify group exists in database
    group = execute_query(
        "SELECT * FROM groups WHERE id = %s",
        (body["id"],),
        fetch_one=True
    )
    assert group is not None
    assert group["name"] == "Integration Test Group"

    # Verify membership exists
    membership = execute_query(
        "SELECT * FROM group_memberships WHERE group_id = %s AND user_id = %s",
        (body["id"], sample_profile["id"]),
        fetch_one=True
    )
    assert membership is not None
    assert membership["role"] == "admin"


def test_get_groups_for_user(clean_db: Any, sample_profile: dict[str, Any], sample_group: dict[str, Any]) -> None:
    """Test retrieving all groups for a user."""
    from handlers.groups import get_groups

    response = get_groups(sample_profile["id"])

    assert response["statusCode"] == 200

    body = json.loads(response["body"])
    assert "groups" in body
    assert len(body["groups"]) == 1
    assert body["groups"][0]["id"] == sample_group["id"]
    assert body["groups"][0]["role"] == "admin"


def test_get_group_detail(clean_db: Any, sample_profile: dict[str, Any], sample_group: dict[str, Any]) -> None:
    """Test retrieving detailed group information."""
    from handlers.groups import get_group_detail

    response = get_group_detail(sample_profile["id"], sample_group["id"])

    assert response["statusCode"] == 200

    body = json.loads(response["body"])
    assert body["group"]["id"] == sample_group["id"]
    assert len(body["members"]) == 1
    assert body["members"][0]["user_id"] == sample_profile["id"]
    assert body["members"][0]["role"] == "admin"


def test_get_group_detail_not_member(clean_db: Any, sample_group: dict[str, Any]) -> None:
    """Test that non-members cannot access group details."""
    from handlers.groups import get_group_detail

    non_member_id = str(uuid4())

    response = get_group_detail(non_member_id, sample_group["id"])

    assert response["statusCode"] == 403


def test_update_group_as_admin(clean_db: Any, sample_profile: dict[str, Any], sample_group: dict[str, Any]) -> None:
    """Test updating a group as admin."""
    from handlers.groups import update_group

    event = {
        "body": json.dumps({
            "name": "Updated Group Name",
            "description": "Updated description"
        })
    }

    response = update_group(event, sample_profile["id"], sample_group["id"])

    assert response["statusCode"] == 200

    body = json.loads(response["body"])
    assert body["name"] == "Updated Group Name"
    assert body["description"] == "Updated description"


def test_update_group_as_non_admin(clean_db: Any, sample_group: dict[str, Any]) -> None:
    """Test that non-admins cannot update groups."""
    from handlers.groups import update_group

    # Create a member (non-admin) user
    member_id = str(uuid4())
    execute_update(
        "INSERT INTO profiles (id, email, name) VALUES (%s, %s, %s)",
        (member_id, f"member-{uuid4()}@example.com", "Member User")
    )
    execute_update(
        "INSERT INTO group_memberships (user_id, group_id, role) VALUES (%s, %s, %s)",
        (member_id, sample_group["id"], "member")
    )

    event = {
        "body": json.dumps({
            "name": "Hacked Name"
        })
    }

    response = update_group(event, member_id, sample_group["id"])

    assert response["statusCode"] == 403


def test_delete_group_as_admin(clean_db: Any, sample_profile: dict[str, Any], sample_group: dict[str, Any]) -> None:
    """Test deleting a group as admin."""
    from handlers.groups import delete_group

    response = delete_group(sample_profile["id"], sample_group["id"])

    assert response["statusCode"] == 204

    # Verify group is deleted
    group = execute_query(
        "SELECT * FROM groups WHERE id = %s",
        (sample_group["id"],),
        fetch_one=True
    )
    assert group is None

    # Verify memberships are also deleted (CASCADE)
    memberships = execute_query(
        "SELECT * FROM group_memberships WHERE group_id = %s",
        (sample_group["id"],)
    )
    assert len(memberships) == 0


def test_multiple_users_in_group(clean_db: Any, sample_profile: dict[str, Any], sample_group: dict[str, Any]) -> None:
    """Test group with multiple members."""
    # Add another member
    member_id = str(uuid4())
    execute_update(
        "INSERT INTO profiles (id, email, name) VALUES (%s, %s, %s)",
        (member_id, f"member2-{uuid4()}@example.com", "Second Member")
    )
    execute_update(
        "INSERT INTO group_memberships (user_id, group_id, role) VALUES (%s, %s, %s)",
        (member_id, sample_group["id"], "member")
    )

    from handlers.groups import get_group_detail

    response = get_group_detail(sample_profile["id"], sample_group["id"])

    assert response["statusCode"] == 200

    body = json.loads(response["body"])
    assert len(body["members"]) == 2

    # Verify member count
    response_list = get_groups(sample_profile["id"])
    body_list = json.loads(response_list["body"])
    assert body_list["groups"][0]["member_count"] == 2


def get_groups(user_id: str) -> dict[str, Any]:
    """Helper to call get_groups handler."""
    from handlers.groups import get_groups as handler_get_groups
    return handler_get_groups(user_id)
