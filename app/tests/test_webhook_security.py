"""
Tests for WhatsApp Webhook Security (HMAC-SHA256 Signature Verification)
"""
import pytest
import hmac
import hashlib
from fastapi import Request, HTTPException, status
from unittest.mock import Mock, AsyncMock, patch
from app.services.security import validate_whatsapp_signature
from app.config import settings

@pytest.fixture
def mock_request():
    request = AsyncMock(spec=Request)
    request.headers = {}
    request.body = AsyncMock(return_value=b'{"test": "data"}')
    return request

@pytest.mark.asyncio
async def test_skip_verification_if_no_secret(mock_request):
    """Should skip verification if whatsapp_app_secret is not configured"""
    with patch("app.services.security.settings.whatsapp_app_secret", ""):
        # Should not raise any exception
        await validate_whatsapp_signature(mock_request)

@pytest.mark.asyncio
async def test_valid_signature(mock_request):
    """Should accept request with valid signature"""
    secret = "test_secret"
    body = b'{"test": "data"}'

    # Calculate valid signature
    signature = hmac.new(
        key=secret.encode(),
        msg=body,
        digestmod=hashlib.sha256
    ).hexdigest()

    mock_request.headers = {"X-Hub-Signature-256": f"sha256={signature}"}
    mock_request.body.return_value = body

    with patch("app.services.security.settings.whatsapp_app_secret", secret):
        # Should not raise exception
        await validate_whatsapp_signature(mock_request)

@pytest.mark.asyncio
async def test_invalid_signature(mock_request):
    """Should reject request with invalid signature"""
    secret = "test_secret"
    body = b'{"test": "data"}'

    mock_request.headers = {"X-Hub-Signature-256": "sha256=invalid_signature"}
    mock_request.body.return_value = body

    with patch("app.services.security.settings.whatsapp_app_secret", secret):
        with pytest.raises(HTTPException) as exc_info:
            await validate_whatsapp_signature(mock_request)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid signature" in exc_info.value.detail

@pytest.mark.asyncio
async def test_missing_signature_header(mock_request):
    """Should reject request missing signature header when secret is configured"""
    secret = "test_secret"

    mock_request.headers = {}  # No signature header

    with patch("app.services.security.settings.whatsapp_app_secret", secret):
        with pytest.raises(HTTPException) as exc_info:
            await validate_whatsapp_signature(mock_request)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Missing signature" in exc_info.value.detail

@pytest.mark.asyncio
async def test_signature_without_prefix(mock_request):
    """Should handle signature without 'sha256=' prefix if necessary (though Meta sends it)"""
    secret = "test_secret"
    body = b'{"test": "data"}'

    # Calculate valid signature
    signature = hmac.new(
        key=secret.encode(),
        msg=body,
        digestmod=hashlib.sha256
    ).hexdigest()

    # Simulate header without prefix (just in case)
    mock_request.headers = {"X-Hub-Signature-256": signature}
    mock_request.body.return_value = body

    with patch("app.services.security.settings.whatsapp_app_secret", secret):
        # Should verify correctly even without prefix handling logic if implemented that way?
        # My implementation handles both with/without prefix logic:
        # if signature_header.startswith("sha256="): ... else: ...
        await validate_whatsapp_signature(mock_request)
