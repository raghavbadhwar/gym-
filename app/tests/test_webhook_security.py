import hmac
import hashlib
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import Request, HTTPException
from app.services.security import validate_whatsapp_signature
from app.config import settings

@pytest.mark.asyncio
async def test_validate_signature_no_secret():
    """Test validation skips when secret is not configured"""
    # Mock settings.whatsapp_app_secret to be empty
    with patch("app.services.security.settings") as mock_settings:
        mock_settings.whatsapp_app_secret = ""

        request = MagicMock(spec=Request)

        # Should not raise exception
        result = await validate_whatsapp_signature(request, None)
        assert result is None

@pytest.mark.asyncio
async def test_validate_signature_missing_header():
    """Test validation fails when header is missing but secret is configured"""
    with patch("app.services.security.settings") as mock_settings:
        mock_settings.whatsapp_app_secret = "test_secret"

        request = MagicMock(spec=Request)

        with pytest.raises(HTTPException) as excinfo:
            await validate_whatsapp_signature(request, None)

        assert excinfo.value.status_code == 401
        assert "Missing signature header" in excinfo.value.detail

@pytest.mark.asyncio
async def test_validate_signature_invalid_format():
    """Test validation fails when header format is invalid"""
    with patch("app.services.security.settings") as mock_settings:
        mock_settings.whatsapp_app_secret = "test_secret"

        request = MagicMock(spec=Request)
        request.body = AsyncMock(return_value=b'{"test": "data"}')

        # Missing sha256= prefix (though replace handles it gracefully by not changing string if not found,
        # but compare_digest will fail if format doesn't match expected hex)
        # Actually my code does: signature = x_hub_signature_256.replace("sha256=", "")
        # If input is "invalid_hash", it remains "invalid_hash"
        # Then hmac compares it against hex digest.

        invalid_sig = "invalid_hash"

        with pytest.raises(HTTPException) as excinfo:
            await validate_whatsapp_signature(request, invalid_sig)

        assert excinfo.value.status_code == 403

@pytest.mark.asyncio
async def test_validate_signature_invalid_signature():
    """Test validation fails when signature is incorrect"""
    with patch("app.services.security.settings") as mock_settings:
        mock_settings.whatsapp_app_secret = "test_secret"

        request = MagicMock(spec=Request)
        request.body = AsyncMock(return_value=b'{"test": "data"}')

        # Incorrect signature
        invalid_sig = "sha256=0000000000000000000000000000000000000000000000000000000000000000"

        with pytest.raises(HTTPException) as excinfo:
            await validate_whatsapp_signature(request, invalid_sig)

        assert excinfo.value.status_code == 403
        assert "Invalid signature" in excinfo.value.detail

@pytest.mark.asyncio
async def test_validate_signature_valid_signature():
    """Test validation passes when signature is valid"""
    secret = "test_secret"
    body = b'{"test": "data"}'

    # Calculate valid signature
    expected_hash = hmac.new(
        secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    valid_sig = f"sha256={expected_hash}"

    with patch("app.services.security.settings") as mock_settings:
        mock_settings.whatsapp_app_secret = secret

        request = MagicMock(spec=Request)
        request.body = AsyncMock(return_value=body)

        # Should not raise exception
        result = await validate_whatsapp_signature(request, valid_sig)
        assert result is None
