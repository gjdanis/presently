"""Tests for profile handler."""

import json
from typing import Any
from unittest.mock import MagicMock, patch

from handlers.profile import get_profile, handler, update_profile


@patch("handlers.profile.require_auth")
@patch("handlers.profile.get_profile")
def test_handler_get_profile(mock_get: MagicMock, mock_auth: MagicMock) -> None:
    """Test profile handler GET endpoint."""
    from common.models import AuthenticatedUser
    from uuid import UUID

    mock_auth.return_value = (
        AuthenticatedUser(
            sub=UUID("12345678-1234-5678-1234-567812345678"),
            email="test@example.com",
            name="Test User",
        ),
        {},
    )
    mock_get.return_value = {"statusCode": 200}

    event: dict[str, Any] = {"httpMethod": "GET", "path": "/profile", "headers": {}}

    response = handler(event, None)

    assert response["statusCode"] == 200
    mock_get.assert_called_once()


@patch("handlers.profile.require_auth")
def test_handler_unauthorized(mock_auth: MagicMock) -> None:
    """Test profile handler with unauthorized request."""
    mock_auth.return_value = (None, {"statusCode": 401})

    event: dict[str, Any] = {"httpMethod": "GET", "path": "/profile", "headers": {}}

    response = handler(event, None)

    assert response["statusCode"] == 401


@patch("handlers.profile.execute_query")
def test_get_profile_success(mock_query: MagicMock) -> None:
    """Test successful profile retrieval."""
    from datetime import datetime

    mock_query.return_value = {
        "id": "12345678-1234-5678-1234-567812345678",
        "email": "test@example.com",
        "name": "Test User",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }

    response = get_profile("12345678-1234-5678-1234-567812345678")

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["email"] == "test@example.com"


@patch("handlers.profile.execute_query")
def test_get_profile_not_found(mock_query: MagicMock) -> None:
    """Test profile not found."""
    mock_query.return_value = None

    response = get_profile("non-existent-id")

    assert response["statusCode"] == 404


@patch("handlers.profile.execute_query")
def test_update_profile_success(mock_query: MagicMock) -> None:
    """Test successful profile update."""
    from datetime import datetime

    mock_query.return_value = {
        "id": "12345678-1234-5678-1234-567812345678",
        "email": "test@example.com",
        "name": "Updated Name",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }

    event: dict[str, Any] = {"body": json.dumps({"name": "Updated Name"})}

    response = update_profile(event, "12345678-1234-5678-1234-567812345678")

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["name"] == "Updated Name"
