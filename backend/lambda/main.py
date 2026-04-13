"""
Presently FastAPI Application

This application works both locally (via uvicorn) and on AWS Lambda (via Mangum).
"""

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from middleware import LoggingMiddleware
from routers import feedback, groups, invitations, photos, profile, purchases, wishlist

# Create FastAPI app
app = FastAPI(
    title="Presently API",
    description="Gift wishlist and group management API",
    version="1.0.0",
    docs_url="/docs" if os.getenv("ENVIRONMENT") == "local" else None,  # Only enable docs locally
    redoc_url="/redoc" if os.getenv("ENVIRONMENT") == "local" else None,
)

# Add logging middleware (first, so it wraps everything)
app.add_middleware(LoggingMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(feedback.router, prefix="/feedback", tags=["Feedback"])
app.include_router(profile.router, prefix="/profile", tags=["Profile"])
app.include_router(groups.router, prefix="/groups", tags=["Groups"])
app.include_router(wishlist.router, prefix="/wishlist", tags=["Wishlist"])
app.include_router(purchases.router, prefix="/purchases", tags=["Purchases"])
app.include_router(invitations.router, prefix="/invitations", tags=["Invitations"])
app.include_router(photos.router, prefix="/photos", tags=["Photos"])


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - health check."""
    return {
        "status": "healthy",
        "service": "Presently API",
        "environment": os.getenv("ENVIRONMENT", "unknown"),
    }


@app.get("/version", tags=["Health"])
async def version():
    """Returns the deployed git commit SHA."""
    return {
        "commit": os.getenv("GIT_COMMIT", "unknown"),
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": os.getenv("ENVIRONMENT", "unknown"),
        "database": os.getenv("DATABASE_URL", "").split("@")[-1].split("/")[0]
        if os.getenv("DATABASE_URL")
        else "not configured",
    }


# Mangum handler for AWS Lambda
# Configure Mangum to handle API Gateway's stage prefix
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    """Lambda handler with logging."""
    logger.info(f"Received event: {event}")
    logger.info(f"Request path: {event.get('rawPath', event.get('path', 'unknown'))}")

    # Use Mangum to handle the request
    mangum_handler = Mangum(app, lifespan="off")
    response = mangum_handler(event, context)

    logger.info(f"Response status: {response.get('statusCode', 'unknown')}")
    return response


# For local development
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    print(
        f"""
╔════════════════════════════════════════════════════════════════╗
║                Presently FastAPI Server                        ║
╚════════════════════════════════════════════════════════════════╝

🚀 Server: http://localhost:{port}
📚 API Docs: http://localhost:{port}/docs
📖 ReDoc: http://localhost:{port}/redoc
🗄️  Database: {os.getenv('DATABASE_URL', 'Not configured').split('@')[-1] if os.getenv('DATABASE_URL') else 'Not configured'}
🌍 Environment: {os.getenv('ENVIRONMENT', 'local')}

Press Ctrl+C to stop
"""
    )

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,  # Auto-reload on code changes
    )
