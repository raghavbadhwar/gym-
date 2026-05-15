import secrets
from fastapi import Header, HTTPException, status
from app.config import settings

async def get_admin_api_key(x_admin_key: str = Header(None, alias="X-Admin-Key")):
    """
    Dependency to validate the Admin API Key.

    Usage:
        @router.get("/protected", dependencies=[Depends(get_admin_api_key)])
        def protected_route(): ...
    """
    # 1. Check if the server is configured securely
    if not settings.admin_api_key:
        # If no key is configured, block all admin access for security.
        # This prevents default-allow behavior if the env var is forgotten.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server Misconfiguration: ADMIN_API_KEY is not set. Admin endpoints are disabled."
        )

    # 2. Check if the client provided a key
    if x_admin_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication header: X-Admin-Key"
        )

    # 3. Validate the key safely (constant-time comparison)
    if not secrets.compare_digest(x_admin_key, settings.admin_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Admin API Key"
        )

    return x_admin_key
