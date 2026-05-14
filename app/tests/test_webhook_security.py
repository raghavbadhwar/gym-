import pytest
from unittest.mock import AsyncMock, patch
from fastapi import Request, HTTPException
from app.services.security import validate_whatsapp_signature

@pytest.mark.asyncio
async def test_validate_signature_missing_secret():
    # If secret is missing, it should just log a warning and return
    # We need to patch settings.whatsapp_app_secret
    with patch("app.services.security.settings") as mock_settings:
        mock_settings.whatsapp_app_secret = ""
        request = AsyncMock(spec=Request)

        # Should not raise exception
        await validate_whatsapp_signature(request)

@pytest.mark.asyncio
async def test_validate_signature_missing_header():
    with patch("app.services.security.settings") as mock_settings:
        mock_settings.whatsapp_app_secret = "secret123"
        request = AsyncMock(spec=Request)
        request.headers.get.return_value = None

        with pytest.raises(HTTPException) as excinfo:
            await validate_whatsapp_signature(request)
        assert excinfo.value.status_code == 403
        assert excinfo.value.detail == "Missing signature header"

@pytest.mark.asyncio
async def test_validate_signature_invalid_format():
    with patch("app.services.security.settings") as mock_settings:
        mock_settings.whatsapp_app_secret = "secret123"
        request = AsyncMock(spec=Request)
        request.headers.get.return_value = "invalidformat"

        with pytest.raises(HTTPException) as excinfo:
            await validate_whatsapp_signature(request)
        assert excinfo.value.status_code == 403
        assert excinfo.value.detail == "Invalid signature format"

@pytest.mark.asyncio
async def test_validate_signature_valid():
    with patch("app.services.security.settings") as mock_settings:
        mock_settings.whatsapp_app_secret = "secret123"

        # Body and expected signature
        body_content = b'{"object":"whatsapp_business_account"}'
        # HMAC-SHA256("secret123", body_content)
        import hmac
        import hashlib
        expected_hmac = hmac.new(b"secret123", body_content, hashlib.sha256).hexdigest()
        signature = f"sha256={expected_hmac}"

        request = AsyncMock(spec=Request)
        request.headers.get.return_value = signature
        request.body.return_value = body_content

        # Should not raise exception
        await validate_whatsapp_signature(request)

@pytest.mark.asyncio
async def test_validate_signature_invalid_hash():
    with patch("app.services.security.settings") as mock_settings:
        mock_settings.whatsapp_app_secret = "secret123"

        body_content = b'{"object":"whatsapp_business_account"}'
        signature = "sha256=invalidhash12345"

        request = AsyncMock(spec=Request)
        request.headers.get.return_value = signature
        request.body.return_value = body_content

        with pytest.raises(HTTPException) as excinfo:
            await validate_whatsapp_signature(request)
        assert excinfo.value.status_code == 403
        assert excinfo.value.detail == "Invalid signature"
