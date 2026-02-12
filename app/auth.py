from fastapi import Security, HTTPException, status, Depends
from fastapi.security import APIKeyHeader
from loguru import logger
from app.config import settings
import secrets

# Define the API Key header scheme
api_key_header = APIKeyHeader(name="X-Admin-Key", auto_error=False)

async def get_admin_api_key(api_key: str = Security(api_key_header)):
    """
    Dependency to validate the Admin API Key.
    Ensures that sensitive endpoints are protected.
    """
    if not settings.admin_api_key:
        logger.error("Admin API Key not configured! Set ADMIN_API_KEY in .env")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admin API not configured",
        )

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Admin-Key header",
        )

    # Use constant-time comparison to prevent timing attacks
    if not secrets.compare_digest(api_key, settings.admin_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )

    return api_key
