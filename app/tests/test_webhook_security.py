
import json
import hmac
import hashlib
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app

# Create a test client
client = TestClient(app)

def calculate_signature(secret: str, body: bytes) -> str:
    """Helper to calculate HMAC-SHA256 signature"""
    signature = hmac.new(
        key=secret.encode("utf-8"),
        msg=body,
        digestmod=hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"

def test_webhook_valid_signature():
    """Test webhook with valid signature"""
    secret = "test_secret_123"
    payload = {"object": "whatsapp_business_account", "entry": []}
    body = json.dumps(payload).encode("utf-8")
    signature = calculate_signature(secret, body)

    # Mock the secret in settings
    # We patch where it is used in the router
    with patch("app.routers.webhooks.settings.whatsapp_app_secret", secret):
        response = client.post(
            "/api/v1/webhooks/whatsapp",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": signature
            }
        )

        # Should be 200 OK
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

def test_webhook_invalid_signature():
    """Test webhook with invalid signature"""
    secret = "test_secret_123"
    payload = {"object": "whatsapp_business_account", "entry": []}
    body = json.dumps(payload).encode("utf-8")

    # Generate signature with WRONG secret
    signature = calculate_signature("wrong_secret", body)

    with patch("app.routers.webhooks.settings.whatsapp_app_secret", secret):
        response = client.post(
            "/api/v1/webhooks/whatsapp",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": signature
            }
        )

        # Should be 200 OK but with error message (the router catches exceptions)
        # Wait, the router catches exceptions and returns 200 with error message.
        # Let's check app/routers/webhooks.py again.
        # Yes: except Exception as e: return {"status": "error", "message": str(e)}

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert "403: Invalid signature" in data["message"]

def test_webhook_missing_signature():
    """Test webhook with missing signature header"""
    secret = "test_secret_123"
    payload = {"object": "whatsapp_business_account", "entry": []}
    body = json.dumps(payload).encode("utf-8")

    with patch("app.routers.webhooks.settings.whatsapp_app_secret", secret):
        response = client.post(
            "/api/v1/webhooks/whatsapp",
            content=body,
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert "403: Missing signature header" in data["message"]

def test_webhook_no_secret_configured():
    """Test webhook when no secret is configured (should skip verification)"""
    payload = {"object": "whatsapp_business_account", "entry": []}
    body = json.dumps(payload).encode("utf-8")

    # Patch secret to be empty string
    with patch("app.routers.webhooks.settings.whatsapp_app_secret", ""):
        response = client.post(
            "/api/v1/webhooks/whatsapp",
            content=body,
            headers={"Content-Type": "application/json"}
        )

        # Should succeed because verification is skipped
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
