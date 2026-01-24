"""Tests for request validators."""

import json
from typing import Any
from uuid import UUID

from common.models import GroupCreate
from common.validators import (
    get_path_parameter,
    get_query_parameter,
    validate_request_body,
    validate_uuid,
)


def test_validate_request_body_success() -> None:
    """Test successful request body validation."""
    event: dict[str, Any] = {"body": json.dumps({"name": "Test Group", "description": "Test"})}

    result, error_response = validate_request_body(event, GroupCreate)

    assert error_response is None
    assert result is not None
    assert result.name == "Test Group"
    assert result.description == "Test"


def test_validate_request_body_missing() -> None:
    """Test validation with missing body."""
    event: dict[str, Any] = {}

    result, error_response = validate_request_body(event, GroupCreate)

    assert result is None
    assert error_response is not None
    assert error_response["statusCode"] == 400


def test_validate_request_body_invalid_json() -> None:
    """Test validation with invalid JSON."""
    event: dict[str, Any] = {"body": "invalid json"}

    result, error_response = validate_request_body(event, GroupCreate)

    assert result is None
    assert error_response is not None
    assert error_response["statusCode"] == 400


def test_validate_request_body_validation_error() -> None:
    """Test validation with Pydantic validation error."""
    event: dict[str, Any] = {"body": json.dumps({"name": ""})}  # Empty name should fail

    result, error_response = validate_request_body(event, GroupCreate)

    assert result is None
    assert error_response is not None
    assert error_response["statusCode"] == 400


def test_validate_uuid_success() -> None:
    """Test successful UUID validation."""
    uuid_str = "12345678-1234-5678-1234-567812345678"

    result, error_response = validate_uuid(uuid_str)

    assert error_response is None
    assert isinstance(result, UUID)
    assert str(result) == uuid_str


def test_validate_uuid_invalid() -> None:
    """Test UUID validation with invalid UUID."""
    result, error_response = validate_uuid("not-a-uuid")

    assert result is None
    assert error_response is not None
    assert error_response["statusCode"] == 400


def test_get_path_parameter_success() -> None:
    """Test getting path parameter."""
    event: dict[str, Any] = {"pathParameters": {"groupId": "test-id"}}

    result, error_response = get_path_parameter(event, "groupId")

    assert error_response is None
    assert result == "test-id"


def test_get_path_parameter_uuid() -> None:
    """Test getting path parameter as UUID."""
    uuid_str = "12345678-1234-5678-1234-567812345678"
    event: dict[str, Any] = {"pathParameters": {"groupId": uuid_str}}

    result, error_response = get_path_parameter(event, "groupId", is_uuid=True)

    assert error_response is None
    assert isinstance(result, UUID)


def test_get_path_parameter_missing() -> None:
    """Test getting missing path parameter."""
    event: dict[str, Any] = {"pathParameters": {}}

    result, error_response = get_path_parameter(event, "groupId")

    assert result is None
    assert error_response is not None
    assert error_response["statusCode"] == 400


def test_get_query_parameter_success() -> None:
    """Test getting query parameter."""
    event: dict[str, Any] = {"queryStringParameters": {"page": "1"}}

    result, error_response = get_query_parameter(event, "page")

    assert error_response is None
    assert result == "1"


def test_get_query_parameter_optional() -> None:
    """Test getting optional query parameter."""
    event: dict[str, Any] = {"queryStringParameters": {}}

    result, error_response = get_query_parameter(event, "page", required=False)

    assert error_response is None
    assert result is None


def test_get_query_parameter_required_missing() -> None:
    """Test getting required query parameter that's missing."""
    event: dict[str, Any] = {"queryStringParameters": {}}

    result, error_response = get_query_parameter(event, "page", required=True)

    assert result is None
    assert error_response is not None
    assert error_response["statusCode"] == 400
