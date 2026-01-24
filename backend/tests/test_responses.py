"""Tests for response utilities."""

import json

from common.responses import (
    conflict,
    created,
    error,
    forbidden,
    no_content,
    not_found,
    server_error,
    success,
    unauthorized,
)
from pydantic import BaseModel


class TestModel(BaseModel):
    """Test Pydantic model."""

    id: str
    name: str


def test_success_response() -> None:
    """Test successful response."""
    data = {"message": "Success"}
    response = success(data)

    assert response["statusCode"] == 200
    assert response["headers"]["Content-Type"] == "application/json"
    assert json.loads(response["body"]) == data


def test_success_with_pydantic() -> None:
    """Test successful response with Pydantic model."""
    model = TestModel(id="123", name="Test")
    response = success(model)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["id"] == "123"
    assert body["name"] == "Test"


def test_created_response() -> None:
    """Test created response."""
    data = {"id": "123"}
    response = created(data)

    assert response["statusCode"] == 201
    assert json.loads(response["body"]) == data


def test_no_content_response() -> None:
    """Test no content response."""
    response = no_content()

    assert response["statusCode"] == 204
    assert response["body"] == ""


def test_error_response() -> None:
    """Test error response."""
    response = error("Test error", 400)

    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert body["error"] == "Test error"


def test_error_with_details() -> None:
    """Test error response with details."""
    details = {"field": "name", "message": "Required"}
    response = error("Validation error", 400, details=details)

    body = json.loads(response["body"])
    assert body["error"] == "Validation error"
    assert body["details"] == details


def test_unauthorized_response() -> None:
    """Test unauthorized response."""
    response = unauthorized()

    assert response["statusCode"] == 401
    body = json.loads(response["body"])
    assert "error" in body


def test_forbidden_response() -> None:
    """Test forbidden response."""
    response = forbidden("Access denied")

    assert response["statusCode"] == 403
    body = json.loads(response["body"])
    assert body["error"] == "Access denied"


def test_not_found_response() -> None:
    """Test not found response."""
    response = not_found("Resource not found")

    assert response["statusCode"] == 404
    body = json.loads(response["body"])
    assert body["error"] == "Resource not found"


def test_conflict_response() -> None:
    """Test conflict response."""
    response = conflict("Duplicate entry")

    assert response["statusCode"] == 409
    body = json.loads(response["body"])
    assert body["error"] == "Duplicate entry"


def test_server_error_response() -> None:
    """Test server error response."""
    response = server_error("Internal error")

    assert response["statusCode"] == 500
    body = json.loads(response["body"])
    assert body["error"] == "Internal error"
