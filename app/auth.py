"""
Authentication dependencies for GymBot-Core
"""
import hmac
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from loguru import logger
from app.config import settings

# API Key Header definition
# auto_error=False allows us to handle the missing key with our own logic
api_key_header = APIKeyHeader(name="X-Admin-Key", auto_error=False)


def get_admin_api_key(api_key: str = Security(api_key_header)):
    """
    Dependency to protect admin endpoints.

    Enforces a fail-secure configuration: if ADMIN_API_KEY is not set in settings,
    it blocks access entirely with a 500 error, rather than failing open.
    """
    # 1. Fail Secure: Check if admin API key is configured
    if not settings.admin_api_key:
        logger.critical("ADMIN_API_KEY is not configured! Admin endpoints are disabled for security.")
        # Raise generic 500 to not leak that it's a config issue to the client
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error"
        )

    # 2. Check provided key
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API Key"
        )

    # 3. Validate key securely
    # Use hmac.compare_digest to prevent timing attacks
    if not hmac.compare_digest(api_key, settings.admin_api_key):
        logger.warning("Invalid admin API key attempt")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key"
        )

    return api_key
