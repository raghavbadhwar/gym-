"""
Authentication Module
Handles API Key verification for administrative endpoints.
"""
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from app.config import settings

# Header name for the API key
api_key_header = APIKeyHeader(name="X-Admin-API-Key", auto_error=False)

async def get_admin_api_key(api_key: str = Security(api_key_header)):
    """
    Dependency to validate the Admin API Key.
    Returns the key if valid, raises 401 otherwise.
    """
    if not settings.admin_api_key:
        # If no key is configured, we default to blocking access in production,
        # but for now we'll assume it's required.
        # However, to be safe, if no key is set, we can't authenticate.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admin API Key not configured on server"
        )

    if api_key == settings.admin_api_key:
        return api_key

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing Admin API Key"
    )
