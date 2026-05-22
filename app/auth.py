"""
Authentication Dependencies
"""
import secrets
from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN, HTTP_500_INTERNAL_SERVER_ERROR
from loguru import logger

from app.config import settings

# Define API Key header scheme
api_key_header = APIKeyHeader(name="X-Admin-API-Key", auto_error=False)

async def get_admin_api_key(
    api_key_header: str = Security(api_key_header),
):
    """
    Dependency to validate the Admin API Key.

    Security Rules:
    1. Fail Secure: If admin_api_key is not configured in settings, deny ALL access (500 error).
    2. If key is missing or invalid, deny access (403 error).
    """

    # Fail Secure Check
    if not settings.admin_api_key:
        logger.critical("SECURITY ALERT: Admin API Key is not configured! Blocking all admin requests.")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error: Security Configuration Missing"
        )

    # Use constant-time comparison to prevent timing attacks
    if api_key_header and secrets.compare_digest(api_key_header, settings.admin_api_key):
        return api_key_header

    logger.warning(f"Unauthorized admin access attempt. Key provided: {api_key_header[:4]}***" if api_key_header else "No key provided")
    raise HTTPException(
        status_code=HTTP_403_FORBIDDEN,
        detail="Could not validate credentials"
    )
