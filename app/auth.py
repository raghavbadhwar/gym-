from fastapi import Security, HTTPException, Depends
from fastapi.security import APIKeyHeader
from app.config import get_settings, Settings
import secrets

api_key_header = APIKeyHeader(name="X-Admin-API-Key", auto_error=False)

async def get_admin_api_key(
    api_key: str = Security(api_key_header),
    settings: Settings = Depends(get_settings)
):
    """
    Validates the admin API key from the header.
    Fails securely if key is not configured or invalid.
    """
    if not settings.admin_api_key:
        # Secure default: if no key is configured, deny all admin access
        raise HTTPException(
            status_code=403,
            detail="Admin access is disabled (API key not configured)"
        )

    if not api_key:
        raise HTTPException(
            status_code=403,
            detail="Missing API Key"
        )

    if not secrets.compare_digest(api_key, settings.admin_api_key):
        raise HTTPException(
            status_code=403,
            detail="Invalid API Key"
        )

    return api_key
