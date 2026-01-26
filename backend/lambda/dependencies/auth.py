"""FastAPI authentication dependency."""

import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from common.auth import verify_token
from common.models import AuthenticatedUser
from common.db import execute_query

security = HTTPBearer()


def get_local_user_by_email(email: str) -> AuthenticatedUser | None:
    """
    Get a user from the database by email for local development.

    Args:
        email: User's email address

    Returns:
        AuthenticatedUser if found, None otherwise
    """
    query = "SELECT id, email, name FROM profiles WHERE email = %s"
    result = execute_query(query, (email,), fetch_one=True)

    if not result:
        return None

    return AuthenticatedUser(
        sub=str(result["id"]),
        email=result["email"],
        name=result.get("name", "")
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> AuthenticatedUser:
    """
    FastAPI dependency to get the current authenticated user.

    Verifies the Cognito JWT token and returns the authenticated user.
    In local environment, accepts "local-<username>" tokens that look up users by email.
    Raises 401 if token is invalid.
    """
    token = credentials.credentials

    # Local development bypass: Accept "local-<username>" tokens
    # Token format: "local-alice" where alice is extracted from email alice@example.com
    if os.getenv("ENVIRONMENT") == "local" and token.startswith("local-"):
        username = token.replace("local-", "")
        # Construct email from username (e.g., "alice" -> "alice@example.com")
        email = f"{username}@example.com"

        user = get_local_user_by_email(email)
        if user:
            return user

        # If not found, raise 401
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Local dev user not found: {email}. Make sure to run 'make seed'.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Production: Verify Cognito JWT
    authorization_header = f"Bearer {token}"
    user = verify_token(authorization_header)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False)),
) -> AuthenticatedUser | None:
    """
    FastAPI dependency for optional authentication.

    Returns the authenticated user if valid token provided, None otherwise.
    In local environment, accepts "local-<username>" tokens that look up users by email.
    Does not raise 401 if no token provided.
    """
    if not credentials:
        return None

    token = credentials.credentials

    # Local development bypass: Accept "local-<username>" tokens
    if os.getenv("ENVIRONMENT") == "local" and token.startswith("local-"):
        username = token.replace("local-", "")
        email = f"{username}@example.com"
        return get_local_user_by_email(email)

    # Production: Verify Cognito JWT
    authorization_header = f"Bearer {token}"
    return verify_token(authorization_header)
