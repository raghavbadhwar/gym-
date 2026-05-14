import pytest
import hmac
import hashlib
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app

client = TestClient(app)

def test_webhook_missing_signature_with_secret_configured():
    """Test that requests without signature are rejected when secret is set"""
    with patch("app.services.security.settings.whatsapp_app_secret", "test_secret"):
        response = client.post("/api/v1/webhooks/whatsapp", json={"test": "data"})
        assert response.status_code == 403
        assert response.json()["detail"] == "Missing signature header"

def test_webhook_invalid_signature():
    """Test that requests with invalid signature are rejected"""
    with patch("app.services.security.settings.whatsapp_app_secret", "test_secret"):
        response = client.post(
            "/api/v1/webhooks/whatsapp",
            json={"test": "data"},
            headers={"X-Hub-Signature-256": "sha256=invalid_hash"}
        )
        assert response.status_code == 403
        assert response.json()["detail"] == "Invalid signature"

def test_webhook_valid_signature():
    """Test that requests with valid signature are accepted"""
    secret = "test_secret"
    data = {"test": "data"}
    payload = json.dumps(data).encode()

    # Calculate valid signature
    signature = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    with patch("app.services.security.settings.whatsapp_app_secret", secret):
        # Mock internal services to avoid side effects and errors during processing
        with patch("app.routers.webhooks.whatsapp_service") as mock_ws:
             # Returning None makes the endpoint return early with {"status": "ok"}
             mock_ws.parse_webhook_message.return_value = None

             response = client.post(
                "/api/v1/webhooks/whatsapp",
                content=payload,
                headers={"X-Hub-Signature-256": f"sha256={signature}", "Content-Type": "application/json"}
            )

             assert response.status_code == 200
             assert response.json() == {"status": "ok"}

def test_webhook_no_secret_configured_bypasses_check():
    """Test that verification is skipped if secret is not configured"""
    # Simulate no secret configured (empty string)
    with patch("app.services.security.settings.whatsapp_app_secret", ""):
        with patch("app.routers.webhooks.whatsapp_service") as mock_ws:
            mock_ws.parse_webhook_message.return_value = None

            # Request without signature should pass
            response = client.post(
                "/api/v1/webhooks/whatsapp",
                json={"test": "data"}
            )
            assert response.status_code == 200
