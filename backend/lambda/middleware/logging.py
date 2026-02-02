"""Logging middleware for FastAPI."""

import time
import traceback
from collections.abc import Callable

from common.logger import setup_logger
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = setup_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests and responses with timing."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response details."""
        # Generate request ID (simple timestamp-based)
        request_id = f"{int(time.time() * 1000)}"

        # Get client info
        client_host = request.client.host if request.client else "unknown"

        # Log request
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} - Client: {client_host}"
        )

        # Time the request
        start_time = time.time()

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Log response
            logger.info(
                f"[{request_id}] {request.method} {request.url.path} - "
                f"Status: {response.status_code} - Duration: {duration:.3f}s"
            )

            return response

        except Exception as e:
            # Calculate duration even on error
            duration = time.time() - start_time

            # Log full error with traceback
            logger.error(
                f"[{request_id}] {request.method} {request.url.path} - "
                f"ERROR after {duration:.3f}s",
                exc_info=True  # This includes the full traceback
            )

            # Also log the traceback as a string for better visibility
            logger.error(f"[{request_id}] Traceback:\n{traceback.format_exc()}")

            # Return error response
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "message": str(e),
                    "request_id": request_id,
                },
            )
