"""Pytest configuration and fixtures."""

import os
from typing import Any, Generator
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import pytest


@pytest.fixture(autouse=True)
def mock_env_vars() -> Generator[None, None, None]:
    """Mock environment variables for all tests."""
    with patch.dict(
        os.environ,
        {
            "DATABASE_URL": "postgresql://test:test@localhost/test",
            "COGNITO_USER_POOL_ID": "us-east-1_TEST123",
            "COGNITO_CLIENT_ID": "test-client-id",
            "AWS_REGION": "us-east-1",
            "PHOTOS_BUCKET": "test-photos-bucket",
            "PHOTOS_CDN": "d123456.cloudfront.net",
        },
    ):
        yield


@pytest.fixture
def mock_user() -> dict[str, Any]:
    """Mock authenticated user."""
    return {
        "sub": str(uuid4()),
        "email": "test@example.com",
        "name": "Test User",
    }


@pytest.fixture
def mock_event() -> dict[str, Any]:
    """Mock Lambda event."""
    return {
        "httpMethod": "GET",
        "path": "/test",
        "headers": {"Authorization": "Bearer test-token"},
        "body": None,
        "pathParameters": {},
        "queryStringParameters": {},
    }


@pytest.fixture
def mock_context() -> MagicMock:
    """Mock Lambda context."""
    context = MagicMock()
    context.function_name = "test-function"
    context.memory_limit_in_mb = 512
    context.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test"
    return context


@pytest.fixture
def mock_db_connection() -> Generator[MagicMock, None, None]:
    """Mock database connection."""
    with patch("common.db.get_db_connection") as mock:
        conn = MagicMock()
        cursor = MagicMock()
        conn.cursor.return_value.__enter__ = MagicMock(return_value=cursor)
        conn.cursor.return_value.__exit__ = MagicMock()
        mock.return_value.__enter__ = MagicMock(return_value=conn)
        mock.return_value.__exit__ = MagicMock()
        yield conn


@pytest.fixture
def mock_auth() -> Generator[MagicMock, None, None]:
    """Mock authentication."""
    with patch("common.auth.verify_token") as mock:
        from common.models import AuthenticatedUser

        mock.return_value = AuthenticatedUser(
            sub=UUID("12345678-1234-5678-1234-567812345678"),
            email="test@example.com",
            name="Test User",
        )
        yield mock
