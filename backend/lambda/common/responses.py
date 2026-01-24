"""Standard HTTP response helpers."""

import json
from typing import Any

from pydantic import BaseModel


def _serialize(obj: Any) -> Any:
    """Serialize objects for JSON response."""
    if isinstance(obj, BaseModel):
        return obj.model_dump(mode="json")
    if isinstance(obj, list):
        return [_serialize(item) for item in obj]
    if isinstance(obj, dict):
        return {key: _serialize(value) for key, value in obj.items()}
    return obj


def success(data: Any, status_code: int = 200) -> dict[str, Any]:
    """Return a successful response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": True,
        },
        "body": json.dumps(_serialize(data), default=str),
    }


def error(message: str, status_code: int = 400, details: Any = None) -> dict[str, Any]:
    """Return an error response."""
    body: dict[str, Any] = {"error": message}
    if details:
        body["details"] = details

    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": True,
        },
        "body": json.dumps(body),
    }


def unauthorized(message: str = "Unauthorized") -> dict[str, Any]:
    """Return a 401 Unauthorized response."""
    return error(message, 401)


def forbidden(message: str = "Forbidden") -> dict[str, Any]:
    """Return a 403 Forbidden response."""
    return error(message, 403)


def not_found(message: str = "Resource not found") -> dict[str, Any]:
    """Return a 404 Not Found response."""
    return error(message, 404)


def conflict(message: str = "Resource conflict") -> dict[str, Any]:
    """Return a 409 Conflict response."""
    return error(message, 409)


def server_error(message: str = "Internal server error") -> dict[str, Any]:
    """Return a 500 Internal Server Error response."""
    return error(message, 500)


def created(data: Any) -> dict[str, Any]:
    """Return a 201 Created response."""
    return success(data, 201)


def no_content() -> dict[str, Any]:
    """Return a 204 No Content response."""
    return {
        "statusCode": 204,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": True,
        },
        "body": "",
    }
