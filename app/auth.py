"""
Authentication module for GymBot-Core.
Handles API key validation for administrative endpoints.
"""
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from app.config import settings
import secrets

# Define the API Key header scheme
api_key_header = APIKeyHeader(name="X-Admin-Key", auto_error=False)

def get_admin_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Dependency to validate the Admin API Key.
    Returns the key if valid, otherwise raises HTTP 403.
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing Admin API Key"
        )

    if not secrets.compare_digest(api_key, settings.admin_api_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Admin API Key"
        )

    return api_key
