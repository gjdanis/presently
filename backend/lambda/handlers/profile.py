"""Profile management Lambda handler."""

import time
from typing import Any

from common.auth import require_auth
from common.db import execute_insert, execute_query, execute_update
from common.decorators import handle_cors
from common.logger import setup_logger
from common.models import ProfileCreate, ProfileResponse, ProfileUpdate
from common.responses import error, not_found, server_error, success
from common.validators import validate_request_body

logger = setup_logger(__name__)


@handle_cors("GET,PUT,OPTIONS")
def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Handle /profile endpoints."""
    start_time = time.time()
    request_id = event.get("requestContext", {}).get("requestId", "N/A")

    logger.info(f"Incoming request: {event.get('httpMethod')} {event.get('path')}")

    try:
        http_method = event["httpMethod"]
        path = event["path"]

        # Require authentication
        user, auth_error = require_auth(event)
        if not user:
            logger.warning(f"Authentication failed - request_id: {request_id}")
            return auth_error

        logger.info(f"Authenticated user: {user.email} (user_id: {user.sub})")

        # Route to appropriate function
        response: dict[str, Any]
        if http_method == "GET" and path == "/profile":
            response = get_profile(str(user.sub))
        elif http_method == "PUT" and path == "/profile":
            response = update_profile(event, str(user.sub))
        else:
            response = error("Not Found", 404)

        # Log response
        duration_ms = (time.time() - start_time) * 1000
        status = response.get("statusCode")
        logger.info(f"Request completed - status: {status}, duration: {duration_ms:.2f}ms")

        return response

    except Exception as e:
        logger.error(f"Unhandled error in handler: {str(e)}", exc_info=True)

        error_response = server_error("Internal server error")
        duration_ms = (time.time() - start_time) * 1000
        logger.error(f"Returning 500 error - duration: {duration_ms:.2f}ms")

        return error_response


def get_profile(user_id: str) -> dict[str, Any]:
    """Get user profile."""
    query = """
        SELECT id, email, name, created_at, updated_at
        FROM profiles
        WHERE id = %s
    """

    result = execute_query(query, (user_id,), fetch_one=True)

    if not result:
        return not_found("Profile not found")

    profile = ProfileResponse(**result)
    return success(profile)


def update_profile(event: dict[str, Any], user_id: str) -> dict[str, Any]:
    """Update user profile."""
    # Validate request body
    update_data, validation_error = validate_request_body(event, ProfileUpdate)
    if validation_error:
        return validation_error

    # Build dynamic UPDATE query based on provided fields
    updates = []
    params: list[Any] = []

    if update_data.name is not None:
        updates.append("name = %s")
        params.append(update_data.name)

    if not updates:
        return error("No fields to update", 400)

    params.append(user_id)

    query = f"""
        UPDATE profiles
        SET {', '.join(updates)}
        WHERE id = %s
        RETURNING id, email, name, created_at, updated_at
    """

    result = execute_query(query, tuple(params), fetch_one=True)

    if not result:
        return not_found("Profile not found")

    profile = ProfileResponse(**result)
    return success(profile)


def create_profile_from_cognito(user_id: str, email: str, name: str) -> dict[str, Any] | None:
    """
    Create a profile when a user signs up via Cognito.
    This is typically called from a Cognito post-confirmation Lambda trigger.

    Args:
        user_id: Cognito User Sub (UUID)
        email: User email
        name: User name

    Returns:
        Profile dict or None if creation failed
    """
    query = """
        INSERT INTO profiles (id, email, name)
        VALUES (%s, %s, %s)
        ON CONFLICT (id) DO NOTHING
        RETURNING id, email, name, created_at, updated_at
    """

    result = execute_insert(query, (user_id, email, name))
    return result
