"""
Authentication and Security Module
Handles API key validation for protected endpoints.
"""
from fastapi import Header, HTTPException, status
import secrets
from loguru import logger
from app.config import settings

async def get_admin_api_key(x_admin_key: str = Header(..., description="Admin API Key")):
    """
    Validates the X-Admin-Key header against the configured admin_api_key.

    Security:
    - Raises 500 if server is not configured with an API key (Fail Secure)
    - Uses constant-time comparison to prevent timing attacks
    """
    if not settings.admin_api_key:
        # Critical security check: Do not allow access if no key is set
        logger.critical("SERVER MISCONFIGURATION: Admin API key not set. Blocking all admin access.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error"
        )

    if not secrets.compare_digest(x_admin_key, settings.admin_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Admin API Key"
        )

    return x_admin_key
