
import pytest
import hmac
import hashlib
import json
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)

# Helper to generate signature
def generate_signature(secret: str, body: bytes) -> str:
    signature = hmac.new(
        secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"

@pytest.fixture(autouse=True)
def setup_settings():
    """Set up test settings before each test."""
    original_secret = settings.whatsapp_app_secret
    settings.whatsapp_app_secret = "test_secret_key_123"
    yield
    settings.whatsapp_app_secret = original_secret

def test_webhook_missing_signature_rejected():
    """
    Test that requests without a signature are rejected when secret is set.
    """
    payload = {"object": "whatsapp_business_account", "entry": []}

    response = client.post("/api/v1/webhooks/whatsapp", json=payload)

    assert response.status_code == 403
    assert response.json()["detail"] == "Missing signature"

def test_webhook_invalid_signature_rejected():
    """
    Test that requests with invalid signature are rejected.
    """
    payload = {"object": "whatsapp_business_account", "entry": []}
    headers = {"X-Hub-Signature-256": "sha256=invalid_signature_hex"}

    response = client.post("/api/v1/webhooks/whatsapp", json=payload, headers=headers)

    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid signature"

@patch("app.routers.webhooks.whatsapp_service")
def test_webhook_valid_signature_accepted(mock_whatsapp_service):
    """
    Test that requests with valid signature are accepted.
    We mock whatsapp_service to return None so we don't trigger downstream logic.
    """
    # Mock parse_webhook_message to return None (like a status update)
    # This causes receive_message to return {"status": "ok"} immediately after verification
    mock_whatsapp_service.parse_webhook_message.return_value = None

    payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "123456789",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {"display_phone_number": "123456", "phone_number_id": "123456"},
                    "contacts": [{"profile": {"name": "Test User"}, "wa_id": "1234567890"}],
                    "messages": [{
                        "from": "1234567890",
                        "id": "wamid.HBgLMTIzNDU2Nzg5MA==",
                        "timestamp": "1707234567",
                        "text": {"body": "Hello World"},
                        "type": "text"
                    }]
                },
                "field": "messages"
            }]
        }]
    }

    body_bytes = json.dumps(payload).encode()
    signature = generate_signature("test_secret_key_123", body_bytes)

    headers = {
        "X-Hub-Signature-256": signature,
        "Content-Type": "application/json"
    }

    response = client.post("/api/v1/webhooks/whatsapp", content=body_bytes, headers=headers)

    # Expect 200 OK
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
