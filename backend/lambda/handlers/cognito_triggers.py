"""Cognito Lambda triggers for automatic profile creation."""

import os
from typing import Any

from common.db import execute_insert
from common.logger import setup_logger

logger = setup_logger(__name__)


def post_confirmation_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Cognito Post-Confirmation Trigger.

    Automatically creates a user profile in the database after successful
    Cognito sign-up confirmation.

    This trigger is called after:
    - User confirms email verification
    - Admin confirms user
    - User is auto-confirmed

    Args:
        event: Cognito trigger event with user attributes
        context: Lambda context

    Returns:
        The same event (required by Cognito triggers)
    """
    logger.info("Post-confirmation trigger invoked")

    try:
        # Extract user attributes from Cognito event
        user_attributes = event.get("request", {}).get("userAttributes", {})

        user_id = user_attributes.get("sub")  # Cognito User Sub (UUID)
        email = user_attributes.get("email")
        name = user_attributes.get("name", email.split("@")[0])  # Default to email prefix if no name

        logger.info(f"Creating profile for user: {email} (ID: {user_id})")

        # Insert profile into database
        query = """
            INSERT INTO profiles (id, email, name)
            VALUES (%s, %s, %s)
            ON CONFLICT (id) DO UPDATE
            SET email = EXCLUDED.email,
                name = EXCLUDED.name
            RETURNING id, email, name, created_at
        """

        result = execute_insert(query, (user_id, email, name))

        if result:
            logger.info(f"Profile created successfully for user: {email}")
        else:
            logger.warning(f"Profile may already exist for user: {email}")

    except Exception as e:
        logger.error(f"Failed to create profile: {str(e)}", exc_info=True)
        # Don't raise exception - we don't want to block user signup
        # The profile can be created later via API if needed

    # Must return the event unchanged for Cognito triggers
    return event


def pre_signup_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Cognito Pre-Signup Trigger (optional).

    Can be used to:
    - Auto-confirm users (skip email verification for testing)
    - Validate email domains
    - Custom validation logic

    Args:
        event: Cognito trigger event
        context: Lambda context

    Returns:
        Modified event with autoConfirmUser and autoVerifyEmail
    """
    logger.info("Pre-signup trigger invoked")

    # Auto-confirm users in dev environment (skip email verification)
    env = os.environ.get("ENVIRONMENT", "dev")

    if env == "dev":
        logger.info("Auto-confirming user (dev environment)")
        event["response"]["autoConfirmUser"] = True
        event["response"]["autoVerifyEmail"] = True

    return event
