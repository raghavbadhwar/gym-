from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
import secrets
from app.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

async def verify_api_key(api_key: str = Security(api_key_header)):
    """
    Verify the API key header.
    Raises 401 if invalid.
    """
    if not secrets.compare_digest(api_key, settings.api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )
    return api_key
