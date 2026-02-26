import pytest
from fastapi.testclient import TestClient
from app.main import app
import hmac
import hashlib
import json
from unittest.mock import patch

client = TestClient(app)

SECRET = "test_secret_123"

def generate_signature(body: bytes, secret: str) -> str:
    signature = hmac.new(
        secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"

@pytest.fixture
def mock_settings_secret():
    # Patch the settings object where it is used in app.services.security
    with patch("app.services.security.settings.whatsapp_app_secret", SECRET):
        yield

def test_webhook_missing_signature(mock_settings_secret):
    """Test that requests without signature header are rejected"""
    response = client.post("/api/v1/webhooks/whatsapp", json={"test": "data"})
    assert response.status_code == 403
    assert response.json()["detail"] == "Missing signature header"

def test_webhook_invalid_signature(mock_settings_secret):
    """Test that requests with invalid signature are rejected"""
    response = client.post(
        "/api/v1/webhooks/whatsapp",
        json={"test": "data"},
        headers={"X-Hub-Signature-256": "sha256=invalid_signature"}
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid signature"

def test_webhook_valid_signature(mock_settings_secret):
    """Test that requests with valid signature are accepted"""
    payload = {"object": "whatsapp_business_account", "entry": []}
    body_bytes = json.dumps(payload).encode()
    signature = generate_signature(body_bytes, SECRET)

    response = client.post(
        "/api/v1/webhooks/whatsapp",
        content=body_bytes,
        headers={"X-Hub-Signature-256": signature, "Content-Type": "application/json"}
    )

    # If security check passes, it enters the function.
    # The function catches errors and returns 200, or returns {"status": "ok"}
    assert response.status_code == 200

def test_webhook_no_secret_configured():
    """Test that verification is skipped (but allowed) if secret is not configured"""
    # Ensure secret is empty
    with patch("app.services.security.settings.whatsapp_app_secret", ""):
        payload = {"test": "data"}
        response = client.post("/api/v1/webhooks/whatsapp", json=payload)
        # Should pass (200) because check is skipped and warning logged
        assert response.status_code == 200
