from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from app.config import settings

api_key_header = APIKeyHeader(name="X-Admin-Key", auto_error=False)

async def get_admin_api_key(api_key_header: str = Security(api_key_header)):
    """
    Dependency to validate the Admin API Key.
    Ensures that only authorized requests can access sensitive endpoints.
    """
    if not api_key_header:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing API Key"
        )

    if api_key_header != settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key"
        )

    return api_key_header
