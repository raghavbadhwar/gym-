import secrets
from fastapi import HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader

from app.config import settings

api_key_header = APIKeyHeader(name="X-Admin-API-Key", auto_error=False)

def get_admin_api_key(api_key_header: str = Security(api_key_header)):
    """
    Validate the admin API key for protected endpoints.
    Uses constant-time comparison to prevent timing attacks.
    """
    if not settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error: Admin API key not set"
        )

    if api_key_header:
        if secrets.compare_digest(api_key_header, settings.admin_api_key):
            return api_key_header

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Could not validate credentials"
    )
