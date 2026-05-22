
import pytest
from fastapi import HTTPException
from app.auth import get_admin_api_key
from app.config import settings

@pytest.mark.asyncio
async def test_get_admin_api_key_valid():
    """Test valid API key."""
    key = settings.admin_api_key
    result = await get_admin_api_key(x_admin_api_key=key)
    assert result == key

@pytest.mark.asyncio
async def test_get_admin_api_key_missing():
    """Test missing API key header."""
    with pytest.raises(HTTPException) as excinfo:
        await get_admin_api_key(x_admin_api_key=None)
    assert excinfo.value.status_code == 401
    assert excinfo.value.detail == "Missing authentication header"

@pytest.mark.asyncio
async def test_get_admin_api_key_invalid():
    """Test invalid API key."""
    with pytest.raises(HTTPException) as excinfo:
        await get_admin_api_key(x_admin_api_key="wrong-key")
    assert excinfo.value.status_code == 403
    assert excinfo.value.detail == "Invalid API key"

@pytest.mark.asyncio
async def test_get_admin_api_key_no_config():
    """Test when server config is missing key (fail secure)."""
    # Temporarily clear the setting
    original_key = settings.admin_api_key
    settings.admin_api_key = ""

    try:
        with pytest.raises(HTTPException) as excinfo:
            await get_admin_api_key(x_admin_api_key="some-key")
        assert excinfo.value.status_code == 500
        assert excinfo.value.detail == "Admin API key not configured on server"
    finally:
        # Restore setting
        settings.admin_api_key = original_key
