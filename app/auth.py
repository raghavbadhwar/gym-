from fastapi import HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN
from app.config import get_settings, Settings
import secrets

api_key_header = APIKeyHeader(name="X-Admin-Key", auto_error=False)

async def get_admin_api_key(
    api_key: str = Security(api_key_header),
    settings: Settings = Depends(get_settings)
):
    """
    Validates the X-Admin-Key header against the configured admin_api_key.
    Uses constant-time comparison to prevent timing attacks.
    """
    if not api_key:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Missing API Key"
        )

    if not settings.admin_api_key:
        raise HTTPException(
            status_code=500, detail="Server Configuration Error: Admin API Key not set"
        )

    # Use constant time comparison
    if not secrets.compare_digest(api_key, settings.admin_api_key):
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Invalid API Key"
        )

    return api_key
