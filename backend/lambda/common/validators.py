"""Request validation utilities."""

import json
from typing import Any, Type, TypeVar
from uuid import UUID

from pydantic import BaseModel, ValidationError

from .responses import error

T = TypeVar("T", bound=BaseModel)


def validate_request_body(event: dict[str, Any], model: Type[T]) -> tuple[T | None, dict[str, Any] | None]:
    """
    Validate request body against a Pydantic model.

    Args:
        event: Lambda event dict
        model: Pydantic model class

    Returns:
        Tuple of (validated_model, None) if valid,
        or (None, error_response) if invalid
    """
    body = event.get("body")

    if not body:
        return None, error("Request body is required", 400)

    try:
        # Parse JSON if body is a string
        if isinstance(body, str):
            body_dict = json.loads(body)
        else:
            body_dict = body

        # Validate with Pydantic model
        validated = model(**body_dict)
        return validated, None

    except json.JSONDecodeError:
        return None, error("Invalid JSON in request body", 400)
    except ValidationError as e:
        return None, error("Validation error", 400, details=e.errors())


def validate_uuid(value: str) -> tuple[UUID | None, dict[str, Any] | None]:
    """
    Validate a UUID string.

    Args:
        value: UUID string

    Returns:
        Tuple of (UUID, None) if valid,
        or (None, error_response) if invalid
    """
    try:
        return UUID(value), None
    except (ValueError, AttributeError):
        return None, error(f"Invalid UUID: {value}", 400)


def get_path_parameter(
    event: dict[str, Any], param_name: str, is_uuid: bool = False
) -> tuple[Any, dict[str, Any] | None]:
    """
    Get and optionally validate a path parameter.

    Args:
        event: Lambda event dict
        param_name: Name of the path parameter
        is_uuid: If True, validate as UUID

    Returns:
        Tuple of (parameter_value, None) if valid,
        or (None, error_response) if invalid or missing
    """
    path_params = event.get("pathParameters", {})

    if not path_params or param_name not in path_params:
        return None, error(f"Missing path parameter: {param_name}", 400)

    value = path_params[param_name]

    if is_uuid:
        return validate_uuid(value)

    return value, None


def get_query_parameter(
    event: dict[str, Any], param_name: str, required: bool = False
) -> tuple[str | None, dict[str, Any] | None]:
    """
    Get a query string parameter.

    Args:
        event: Lambda event dict
        param_name: Name of the query parameter
        required: If True, return error if missing

    Returns:
        Tuple of (parameter_value, None) if found or not required,
        or (None, error_response) if required but missing
    """
    query_params = event.get("queryStringParameters", {}) or {}
    value = query_params.get(param_name)

    if required and not value:
        return None, error(f"Missing required query parameter: {param_name}", 400)

    return value, None
