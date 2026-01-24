"""Tests for authentication utilities."""

from typing import Any
from unittest.mock import MagicMock, patch
from uuid import UUID

from common.auth import require_auth, verify_token


def test_verify_token_missing_header() -> None:
    """Test token verification with missing header."""
    result = verify_token(None)
    assert result is None


def test_verify_token_invalid_format() -> None:
    """Test token verification with invalid format."""
    result = verify_token("InvalidToken")
    assert result is None


@patch("common.auth.get_cognito_public_keys")
@patch("common.auth.jwt.get_unverified_headers")
@patch("common.auth.jwt.decode")
def test_verify_token_success(
    mock_decode: MagicMock, mock_headers: MagicMock, mock_keys: MagicMock
) -> None:
    """Test successful token verification."""
    # Mock Cognito public keys
    mock_keys.return_value = {
        "keys": [{"kid": "test-key-id", "kty": "RSA", "use": "sig", "n": "test", "e": "AQAB"}]
    }

    # Mock token headers
    mock_headers.return_value = {"kid": "test-key-id"}

    # Mock decoded payload
    mock_decode.return_value = {
        "sub": "12345678-1234-5678-1234-567812345678",
        "email": "test@example.com",
        "name": "Test User",
    }

    result = verify_token("Bearer test-token")

    assert result is not None
    assert isinstance(result.sub, UUID)
    assert result.email == "test@example.com"
    assert result.name == "Test User"


def test_require_auth_missing_token() -> None:
    """Test require_auth with missing token."""
    event: dict[str, Any] = {"headers": {}}

    user, error_response = require_auth(event)

    assert user is None
    assert error_response is not None
    assert error_response["statusCode"] == 401


@patch("common.auth.verify_token")
def test_require_auth_success(mock_verify: MagicMock) -> None:
    """Test successful authentication requirement."""
    from common.models import AuthenticatedUser

    mock_verify.return_value = AuthenticatedUser(
        sub=UUID("12345678-1234-5678-1234-567812345678"),
        email="test@example.com",
        name="Test User",
    )

    event: dict[str, Any] = {"headers": {"Authorization": "Bearer test-token"}}

    user, error_response = require_auth(event)

    assert error_response == {}
    assert user is not None
    assert user.email == "test@example.com"
