"""
Authentication Module
Handles API key verification for administrative endpoints.
"""
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
import secrets
from app.config import settings

# API Key header definition
api_key_header = APIKeyHeader(name="X-Admin-Key", auto_error=True)


async def get_admin_api_key(api_key: str = Security(api_key_header)):
    """
    Dependency to validate the Admin API Key.

    1. Checks if the server has an admin API key configured.
    2. Validates the provided key against the configured key using constant-time comparison.

    Raises:
        HTTPException(500): If server is not configured with an API key.
        HTTPException(401): If the provided key is invalid.
    """
    # 1. Server Configuration Check
    if not settings.admin_api_key:
        # Security fail-safe: Do not allow access if no key is set on the server
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server Misconfiguration: Admin API Key is not set. Please configure ADMIN_API_KEY."
        )

    # 2. Key Validation
    if not secrets.compare_digest(api_key, settings.admin_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Admin API Key"
        )

    return api_key
