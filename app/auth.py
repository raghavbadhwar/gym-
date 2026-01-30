import secrets
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from app.config import settings

API_KEY_HEADER = APIKeyHeader(name="X-Admin-API-Key", auto_error=False)

async def get_admin_api_key(api_key_header: str = Security(API_KEY_HEADER)):
    """
    Validates the X-Admin-API-Key header.
    Returns the key if valid, otherwise raises HTTP 403.
    """
    if not api_key_header:
         raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API Key",
        )

    if not settings.admin_api_key or not secrets.compare_digest(api_key_header, settings.admin_api_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key",
        )
    return api_key_header
