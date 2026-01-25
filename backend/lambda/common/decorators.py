"""Common decorators for Lambda handlers."""

import json
import traceback
from functools import wraps
from typing import Any, Callable

from .logger import setup_logger

logger = setup_logger(__name__)


def handle_cors(allowed_methods: str = "GET,POST,PUT,DELETE,OPTIONS") -> Callable:
    """
    Decorator to handle CORS preflight OPTIONS requests and errors.

    Args:
        allowed_methods: Comma-separated list of allowed HTTP methods

    Usage:
        @handle_cors("GET,POST,PUT,DELETE,OPTIONS")
        def handler(event, context):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(event: dict[str, Any], context: Any) -> dict[str, Any]:
            cors_headers = {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,Authorization",
                "Access-Control-Allow-Methods": allowed_methods,
                "Access-Control-Allow-Credentials": "true",
            }

            # Handle OPTIONS preflight
            if event.get("httpMethod") == "OPTIONS":
                return {
                    "statusCode": 200,
                    "headers": cors_headers,
                    "body": "",
                }

            # Call the actual handler with error handling
            try:
                response = func(event, context)

                # Ensure CORS headers are present in the response
                if "headers" not in response:
                    response["headers"] = {}
                response["headers"].update(cors_headers)

                return response
            except Exception as e:
                # Log the full error
                logger.error(f"Unhandled exception in {func.__name__}: {str(e)}", exc_info=True)

                # Return error response with CORS headers
                return {
                    "statusCode": 500,
                    "headers": cors_headers,
                    "body": json.dumps({
                        "error": "Internal Server Error",
                        "message": str(e),
                        "type": type(e).__name__,
                    })
                }

        return wrapper
    return decorator
