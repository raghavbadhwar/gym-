from fastapi import Header, HTTPException, status
import secrets
from app.config import settings

async def get_admin_api_key(
    x_admin_key: str = Header(..., description="Admin API Key")
):
    """
    Dependency to verify the Admin API Key.
    """
    if not settings.admin_api_key:
        # If no key is configured, deny all access for security
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admin API Key not configured on server"
        )

    if not secrets.compare_digest(x_admin_key, settings.admin_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Admin API Key"
        )

    return x_admin_key
