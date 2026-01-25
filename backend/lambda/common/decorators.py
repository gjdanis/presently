"""Common decorators for Lambda handlers."""

from functools import wraps
from typing import Any, Callable


def handle_cors(allowed_methods: str = "GET,POST,PUT,DELETE,OPTIONS") -> Callable:
    """
    Decorator to handle CORS preflight OPTIONS requests.

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
            # Handle OPTIONS preflight
            if event.get("httpMethod") == "OPTIONS":
                return {
                    "statusCode": 200,
                    "headers": {
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Headers": "Content-Type,Authorization",
                        "Access-Control-Allow-Methods": allowed_methods,
                        "Access-Control-Allow-Credentials": "true",
                    },
                    "body": "",
                }

            # Call the actual handler
            return func(event, context)

        return wrapper
    return decorator
