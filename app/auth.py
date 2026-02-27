"""
Authentication dependencies for API endpoints.
"""
from fastapi import Header, HTTPException, status
from typing import Optional
import secrets

from app.config import settings

async def get_admin_api_key(
    x_admin_api_key: Optional[str] = Header(None, alias="X-Admin-API-Key")
) -> str:
    """
    Validate the Admin API Key header.

    Args:
        x_admin_api_key: The API key provided in the header.

    Returns:
        The validated API key.

    Raises:
        HTTPException(403): If the key is missing or invalid.
    """
    if not settings.admin_api_key:
        # Fail secure: if no key is configured, deny all access
        # but log a critical error (in a real app)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admin API key not configured on server"
        )

    if not x_admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication header"
        )

    # Constant-time comparison to prevent timing attacks
    if not secrets.compare_digest(x_admin_api_key, settings.admin_api_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key"
        )

    return x_admin_api_key
