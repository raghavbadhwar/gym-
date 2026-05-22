"""
Authentication dependencies
"""
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from app.config import settings

api_key_header = APIKeyHeader(name="X-Admin-API-Key", auto_error=True)

async def get_admin_api_key(api_key: str = Security(api_key_header)):
    """
    Validate the Admin API Key.
    """
    if api_key != settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials"
        )
    return api_key
