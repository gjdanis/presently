"""Cognito trigger handlers for user lifecycle events."""

import logging

from common.db import execute_insert

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def pre_signup_handler(event, context):
    """
    Pre-signup Lambda trigger.

    This runs before a user is created in Cognito.
    We can use it for custom validation or auto-confirmation.
    """
    logger.info(f"Pre-signup trigger invoked for user: {event['userName']}")

    # Auto-confirm the user (skip email verification for dev/testing)
    # In production, you might want to remove this or add custom validation
    event['response']['autoConfirmUser'] = True
    event['response']['autoVerifyEmail'] = True

    return event


def post_confirmation_handler(event, context):
    """
    Post-confirmation Lambda trigger.

    This runs after a user confirms their email.
    We use it to create the user's profile in our database.
    """
    logger.info(f"Post-confirmation trigger invoked for user: {event['userName']}")

    try:
        # Extract user attributes
        user_id = event['request']['userAttributes']['sub']
        email = event['request']['userAttributes']['email']
        name = event['request']['userAttributes'].get('name', email.split('@')[0])

        logger.info(f"Creating profile for user_id={user_id}, email={email}, name={name}")

        # Create profile in database
        query = """
            INSERT INTO profiles (id, email, name)
            VALUES (%s, %s, %s)
            ON CONFLICT (id) DO NOTHING
            RETURNING id, email, name, created_at, updated_at
        """

        result = execute_insert(query, (user_id, email, name))

        if result:
            logger.info(f"Profile created successfully for user {user_id}")
        else:
            logger.info(f"Profile already exists for user {user_id}")

    except Exception as e:
        logger.exception(f"Error creating profile: {str(e)}")
        # Don't fail the signup process even if profile creation fails
        # The user can still sign in and we can create the profile later

    return event
