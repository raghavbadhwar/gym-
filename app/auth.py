import secrets
from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader

from app.config import settings

api_key_header = APIKeyHeader(name="X-Admin-API-Key", auto_error=False)

def get_admin_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Validate the admin API key for protected endpoints.
    Uses constant-time comparison to prevent timing attacks.
    Implements a Fail Secure strategy if the key is not configured.
    """
    if not settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admin API key is not configured on the server. Failing secure."
        )

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing X-Admin-API-Key header"
        )

    if not secrets.compare_digest(api_key, settings.admin_api_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid Admin API Key"
        )

    return api_key
