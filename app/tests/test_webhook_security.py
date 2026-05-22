import pytest
import hmac
import hashlib
from fastapi import Request, HTTPException
from unittest.mock import Mock, AsyncMock, patch
from app.services.security import validate_whatsapp_signature
from app.config import settings

@pytest.fixture
def mock_request():
    request = Mock(spec=Request)
    request.body = AsyncMock(return_value=b'{"object":"whatsapp_business_account", "entry":[]}')
    return request

@pytest.mark.asyncio
async def test_validate_signature_success(mock_request):
    """Test successful signature validation"""
    secret = "my_secret_key"
    body = await mock_request.body()

    # Calculate valid signature
    signature = hmac.new(
        key=secret.encode(),
        msg=body,
        digestmod=hashlib.sha256
    ).hexdigest()

    header = f"sha256={signature}"

    # Mock settings
    with patch.object(settings, 'whatsapp_app_secret', secret):
        # Should not raise exception
        await validate_whatsapp_signature(mock_request, header)

@pytest.mark.asyncio
async def test_validate_signature_mismatch(mock_request):
    """Test signature mismatch"""
    secret = "my_secret_key"
    header = "sha256=invalid_signature"

    with patch.object(settings, 'whatsapp_app_secret', secret):
        with pytest.raises(HTTPException) as excinfo:
            await validate_whatsapp_signature(mock_request, header)
        assert excinfo.value.status_code == 403
        assert excinfo.value.detail == "Invalid signature"

@pytest.mark.asyncio
async def test_validate_signature_missing_header(mock_request):
    """Test missing header when secret is configured"""
    secret = "my_secret_key"

    with patch.object(settings, 'whatsapp_app_secret', secret):
        with pytest.raises(HTTPException) as excinfo:
            await validate_whatsapp_signature(mock_request, None)
        assert excinfo.value.status_code == 403
        assert excinfo.value.detail == "Missing signature header"

@pytest.mark.asyncio
async def test_validate_signature_disabled(mock_request):
    """Test validation skipped when secret is not configured"""
    # Mock settings with empty secret
    with patch.object(settings, 'whatsapp_app_secret', ""):
        # Should not raise exception even without header
        await validate_whatsapp_signature(mock_request, None)

@pytest.mark.asyncio
async def test_validate_signature_invalid_format(mock_request):
    """Test invalid header format"""
    secret = "my_secret_key"
    header = "invalid_format"

    with patch.object(settings, 'whatsapp_app_secret', secret):
        with pytest.raises(HTTPException) as excinfo:
            await validate_whatsapp_signature(mock_request, header)
        assert excinfo.value.status_code == 403
        assert excinfo.value.detail == "Invalid signature format"
