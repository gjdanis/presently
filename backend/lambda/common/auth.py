"""Cognito JWT authentication."""

import os
from typing import Any

import requests
from jose import JWTError, jwt

from .models import AuthenticatedUser
from .responses import unauthorized

# Cache for Cognito public keys
_jwks_cache: dict[str, Any] | None = None


def get_cognito_public_keys() -> dict[str, Any]:
    """Fetch and cache Cognito public keys."""
    global _jwks_cache

    if _jwks_cache is not None:
        return _jwks_cache

    user_pool_id = os.environ.get("COGNITO_USER_POOL_ID")
    region = os.environ.get("AWS_REGION", "us-east-1")

    if not user_pool_id:
        raise ValueError("COGNITO_USER_POOL_ID environment variable is not set")

    keys_url = (
        f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json"
    )

    response = requests.get(keys_url, timeout=10)
    response.raise_for_status()

    _jwks_cache = response.json()
    return _jwks_cache


def verify_token(authorization_header: str | None) -> AuthenticatedUser | None:
    """
    Verify Cognito JWT token and return authenticated user.

    Args:
        authorization_header: Authorization header value (Bearer <token>)

    Returns:
        AuthenticatedUser if valid, None otherwise
    """
    if not authorization_header:
        return None

    # Extract token from "Bearer <token>"
    parts = authorization_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    token = parts[1]

    try:
        # Get Cognito public keys
        jwks = get_cognito_public_keys()

        # Decode token header to get key ID
        headers = jwt.get_unverified_headers(token)
        kid = headers.get("kid")

        if not kid:
            return None

        # Find the matching public key
        key = None
        for jwk in jwks.get("keys", []):
            if jwk.get("kid") == kid:
                key = jwk
                break

        if not key:
            return None

        # Verify and decode the token
        user_pool_id = os.environ.get("COGNITO_USER_POOL_ID")
        region = os.environ.get("AWS_REGION", "us-east-1")
        issuer = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"

        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=os.environ.get("COGNITO_CLIENT_ID"),
            issuer=issuer,
        )

        # Extract user information
        return AuthenticatedUser(
            sub=payload["sub"],
            email=payload.get("email", ""),
            name=payload.get("name"),
        )

    except JWTError:
        return None
    except Exception:
        return None


def require_auth(event: dict[str, Any]) -> tuple[AuthenticatedUser, dict[str, Any]] | tuple[None, dict[str, Any]]:
    """
    Require authentication for a Lambda function.

    Args:
        event: Lambda event dict

    Returns:
        Tuple of (AuthenticatedUser, None) if authenticated,
        or (None, error_response) if not authenticated
    """
    headers = event.get("headers", {})
    authorization = headers.get("Authorization") or headers.get("authorization")

    user = verify_token(authorization)

    if not user:
        return None, unauthorized("Invalid or missing authentication token")

    return user, {}
