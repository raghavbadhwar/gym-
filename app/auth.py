"""
Authentication dependencies for the API.
"""
from fastapi import Security, HTTPException, status, Depends
from fastapi.security import APIKeyHeader
import secrets
from app.config import settings as global_settings, Settings, get_settings

# Define the API Key header scheme
api_key_header = APIKeyHeader(name="X-Admin-Key", auto_error=False)

async def get_admin_api_key(
    api_key: str = Security(api_key_header),
    settings: Settings = Depends(get_settings)
):
    """
    Dependency to validate the Admin API Key.
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin API Key missing",
        )

    # Use constant-time comparison to prevent timing attacks
    if not secrets.compare_digest(api_key, settings.admin_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Admin API Key",
        )

    return api_key
