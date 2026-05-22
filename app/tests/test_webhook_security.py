import pytest
import hmac
import hashlib
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request, HTTPException
from app.services.security import validate_whatsapp_signature

# Helper to generate signature
def generate_signature(secret: str, body: bytes) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

@pytest.mark.asyncio
async def test_validate_signature_valid():
    """Test valid signature with secret set."""
    secret = "test_secret"
    body = b'{"object":"whatsapp_business_account"}'
    signature = generate_signature(secret, body)

    mock_request = MagicMock(spec=Request)
    mock_request.body = AsyncMock(return_value=body)

    with patch("app.services.security.settings") as mock_settings:
        mock_settings.whatsapp_app_secret = secret
        result = await validate_whatsapp_signature(mock_request, signature)
        assert result is True

@pytest.mark.asyncio
async def test_validate_signature_invalid():
    """Test invalid signature with secret set."""
    secret = "test_secret"
    body = b'{"object":"whatsapp_business_account"}'
    signature = "sha256=invalid_signature"

    mock_request = MagicMock(spec=Request)
    mock_request.body = AsyncMock(return_value=body)

    with patch("app.services.security.settings") as mock_settings:
        mock_settings.whatsapp_app_secret = secret
        with pytest.raises(HTTPException) as exc_info:
            await validate_whatsapp_signature(mock_request, signature)
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "Invalid signature"

@pytest.mark.asyncio
async def test_validate_signature_missing_header():
    """Test missing signature header with secret set."""
    secret = "test_secret"

    mock_request = MagicMock(spec=Request)

    with patch("app.services.security.settings") as mock_settings:
        mock_settings.whatsapp_app_secret = secret
        with pytest.raises(HTTPException) as exc_info:
            await validate_whatsapp_signature(mock_request, None)
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "Missing signature header"

@pytest.mark.asyncio
async def test_validate_signature_no_secret():
    """Test verification skipped when secret is not set."""
    mock_request = MagicMock(spec=Request)

    with patch("app.services.security.settings") as mock_settings:
        mock_settings.whatsapp_app_secret = ""
        result = await validate_whatsapp_signature(mock_request, "sha256=whatever")
        assert result is True
