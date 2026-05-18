import pytest
from fastapi import HTTPException, status
from unittest.mock import patch
from app.auth import get_admin_api_key
import secrets

@pytest.mark.asyncio
async def test_get_admin_api_key_success():
    """Test successful API key validation."""
    with patch("app.auth.settings") as mock_settings:
        mock_settings.admin_api_key = "correct_key"

        # Should not raise an exception
        result = get_admin_api_key(api_key="correct_key")
        assert result == "correct_key"


@pytest.mark.asyncio
async def test_get_admin_api_key_missing_from_request():
    """Test when API key is missing from the request header."""
    with patch("app.auth.settings") as mock_settings:
        mock_settings.admin_api_key = "correct_key"

        with pytest.raises(HTTPException) as exc_info:
            get_admin_api_key(api_key=None)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert exc_info.value.detail == "Missing X-Admin-API-Key header"


@pytest.mark.asyncio
async def test_get_admin_api_key_invalid_key():
    """Test when provided API key is invalid."""
    with patch("app.auth.settings") as mock_settings:
        mock_settings.admin_api_key = "correct_key"

        with pytest.raises(HTTPException) as exc_info:
            get_admin_api_key(api_key="wrong_key")

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert exc_info.value.detail == "Invalid Admin API Key"


@pytest.mark.asyncio
async def test_get_admin_api_key_not_configured_fail_secure():
    """Test Fail Secure strategy when server-side API key is not configured."""
    with patch("app.auth.settings") as mock_settings:
        mock_settings.admin_api_key = None

        with pytest.raises(HTTPException) as exc_info:
            get_admin_api_key(api_key="any_key")

        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Admin API key is not configured" in exc_info.value.detail
