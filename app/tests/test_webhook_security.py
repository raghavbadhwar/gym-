import pytest
from fastapi import Request, HTTPException
from unittest.mock import AsyncMock, patch
from app.services.security import validate_whatsapp_signature
import hmac
import hashlib

@pytest.mark.asyncio
async def test_validate_signature_valid():
    """Test validation passes with correct signature."""
    secret = "my_secret_key"
    payload = b'{"object":"whatsapp_business_account"}'

    # Calculate valid signature
    signature = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()

    mock_request = AsyncMock(spec=Request)
    mock_request.body.return_value = payload

    with patch("app.services.security.settings") as mock_settings:
        mock_settings.whatsapp_app_secret = secret

        # Should not raise exception
        await validate_whatsapp_signature(mock_request, x_hub_signature_256=f"sha256={signature}")

@pytest.mark.asyncio
async def test_validate_signature_invalid():
    """Test validation fails with incorrect signature."""
    secret = "my_secret_key"
    payload = b'{"object":"whatsapp_business_account"}'

    mock_request = AsyncMock(spec=Request)
    mock_request.body.return_value = payload

    with patch("app.services.security.settings") as mock_settings:
        mock_settings.whatsapp_app_secret = secret

        with pytest.raises(HTTPException) as exc:
            await validate_whatsapp_signature(mock_request, x_hub_signature_256="sha256=invalid_sig")

        assert exc.value.status_code == 403
        assert "Invalid signature" in exc.value.detail

@pytest.mark.asyncio
async def test_validate_signature_missing_header():
    """Test validation fails when header is missing but secret is configured."""
    secret = "my_secret_key"

    mock_request = AsyncMock(spec=Request)

    with patch("app.services.security.settings") as mock_settings:
        mock_settings.whatsapp_app_secret = secret

        with pytest.raises(HTTPException) as exc:
            await validate_whatsapp_signature(mock_request, x_hub_signature_256=None)

        assert exc.value.status_code == 403
        assert "Missing signature" in exc.value.detail

@pytest.mark.asyncio
async def test_validate_signature_no_secret_configured():
    """Test validation is skipped when no secret is configured."""
    mock_request = AsyncMock(spec=Request)

    with patch("app.services.security.settings") as mock_settings:
        mock_settings.whatsapp_app_secret = ""

        # Should not raise exception even without header
        await validate_whatsapp_signature(mock_request, x_hub_signature_256=None)
