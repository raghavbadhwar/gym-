
import hmac
import hashlib
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)

# Store original secret to restore after tests
ORIGINAL_SECRET = settings.whatsapp_app_secret

@pytest.fixture(autouse=True)
def restore_settings():
    yield
    settings.whatsapp_app_secret = ORIGINAL_SECRET

def test_webhook_signature_valid():
    """Test valid signature verification"""
    settings.whatsapp_app_secret = "test_secret_123"

    # Valid JSON payload
    payload = b'{"object":"whatsapp_business_account","entry":[{"id":"123","changes":[{"value":{"messaging_product":"whatsapp","metadata":{"display_phone_number":"1234567890","phone_number_id":"1234567890"},"contacts":[{"profile":{"name":"Test User"},"wa_id":"1234567890"}],"messages":[{"from":"1234567890","id":"wamid.test","timestamp":"1234567890","text":{"body":"Hello"}}]},"field":"messages"}]}]}'

    # Calculate valid signature
    signature = hmac.new(
        settings.whatsapp_app_secret.encode(),
        msg=payload,
        digestmod=hashlib.sha256
    ).hexdigest()

    response = client.post(
        "/api/v1/webhooks/whatsapp",
        content=payload,
        headers={"X-Hub-Signature-256": f"sha256={signature}"}
    )

    # Should not be 403
    assert response.status_code != 403
    # It will likely return 200 because the endpoint catches exceptions and returns status: error
    assert response.status_code == 200

def test_webhook_signature_invalid():
    """Test invalid signature verification"""
    settings.whatsapp_app_secret = "test_secret_123"

    payload = b'{"test": "data"}'
    invalid_signature = "a" * 64

    response = client.post(
        "/api/v1/webhooks/whatsapp",
        content=payload,
        headers={"X-Hub-Signature-256": f"sha256={invalid_signature}"}
    )

    assert response.status_code == 403
    assert "Invalid signature" in response.json()["detail"]

def test_webhook_signature_missing():
    """Test missing signature verification"""
    settings.whatsapp_app_secret = "test_secret_123"

    payload = b'{"test": "data"}'

    response = client.post(
        "/api/v1/webhooks/whatsapp",
        content=payload
    )

    assert response.status_code == 403
    assert "Missing signature header" in response.json()["detail"]

def test_webhook_signature_disabled():
    """Test when secret is not set (should allow)"""
    settings.whatsapp_app_secret = ""

    payload = b'{"test": "data"}'

    response = client.post(
        "/api/v1/webhooks/whatsapp",
        content=payload
    )

    # Should pass verification
    assert response.status_code == 200
