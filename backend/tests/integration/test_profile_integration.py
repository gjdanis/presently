"""Integration tests for profile endpoints with real database."""

from typing import Any
from uuid import uuid4

import pytest

from handlers.profile import create_profile_from_cognito, get_profile, update_profile


def test_create_profile_from_cognito(clean_db: Any) -> None:
    """Test creating a profile from Cognito signup."""
    user_id = str(uuid4())
    email = "newuser@example.com"
    name = "New User"

    result = create_profile_from_cognito(user_id, email, name)

    assert result is not None
    assert result["id"] == user_id
    assert result["email"] == email
    assert result["name"] == name
    assert result["created_at"] is not None


def test_create_duplicate_profile(clean_db: Any, sample_profile: dict[str, Any]) -> None:
    """Test creating a profile with duplicate ID returns None (ON CONFLICT DO NOTHING)."""
    # Try to create with same ID
    result = create_profile_from_cognito(
        sample_profile["id"],
        "different@example.com",
        "Different Name"
    )

    # Should return None due to ON CONFLICT DO NOTHING
    assert result is None


def test_get_profile_success(clean_db: Any, sample_profile: dict[str, Any]) -> None:
    """Test retrieving an existing profile."""
    response = get_profile(sample_profile["id"])

    assert response["statusCode"] == 200

    import json
    body = json.loads(response["body"])

    assert body["id"] == sample_profile["id"]
    assert body["email"] == sample_profile["email"]
    assert body["name"] == sample_profile["name"]


def test_get_profile_not_found(clean_db: Any) -> None:
    """Test retrieving a non-existent profile."""
    non_existent_id = str(uuid4())

    response = get_profile(non_existent_id)

    assert response["statusCode"] == 404


def test_update_profile_success(clean_db: Any, sample_profile: dict[str, Any]) -> None:
    """Test updating a profile."""
    import json

    event = {
        "body": json.dumps({"name": "Updated Name"})
    }

    response = update_profile(event, sample_profile["id"])

    assert response["statusCode"] == 200

    body = json.loads(response["body"])
    assert body["name"] == "Updated Name"
    assert body["email"] == sample_profile["email"]  # Email should not change


def test_update_profile_not_found(clean_db: Any) -> None:
    """Test updating a non-existent profile."""
    import json

    non_existent_id = str(uuid4())

    event = {
        "body": json.dumps({"name": "New Name"})
    }

    response = update_profile(event, non_existent_id)

    assert response["statusCode"] == 404


def test_update_profile_no_changes(clean_db: Any, sample_profile: dict[str, Any]) -> None:
    """Test updating profile with no fields returns error."""
    import json

    event = {
        "body": json.dumps({})
    }

    response = update_profile(event, sample_profile["id"])

    assert response["statusCode"] == 400
