import pytest
import hmac
import hashlib
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)

# Helper to generate signature
def generate_signature(secret, body):
    return "sha256=" + hmac.new(
        secret.encode(),
        body.encode(),
        hashlib.sha256
    ).hexdigest()

def test_missing_signature_header_with_secret_configured(monkeypatch):
    # Enforce secret presence
    monkeypatch.setattr(settings, "whatsapp_app_secret", "test_secret")

    response = client.post("/api/v1/webhooks/whatsapp", json={"test": "data"})
    assert response.status_code == 403
    assert response.json()["detail"] == "Missing signature header"

def test_invalid_signature_format(monkeypatch):
    monkeypatch.setattr(settings, "whatsapp_app_secret", "test_secret")

    response = client.post(
        "/api/v1/webhooks/whatsapp",
        json={"test": "data"},
        headers={"X-Hub-Signature-256": "invalid_format"}
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid signature format"

def test_invalid_signature_mismatch(monkeypatch):
    monkeypatch.setattr(settings, "whatsapp_app_secret", "test_secret")

    # Generate signature with WRONG secret
    signature = generate_signature("wrong_secret", '{"test": "data"}')

    response = client.post(
        "/api/v1/webhooks/whatsapp",
        content='{"test": "data"}', # Send raw content to match signature
        headers={"X-Hub-Signature-256": signature, "Content-Type": "application/json"}
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid signature"

def test_valid_signature_success(monkeypatch):
    secret = "test_secret"
    monkeypatch.setattr(settings, "whatsapp_app_secret", secret)

    body = '{"object": "whatsapp_business_account"}'
    signature = generate_signature(secret, body)

    # Mock parse_webhook_message to return None so it exits early with 200 OK
    with patch("app.routers.webhooks.whatsapp_service.parse_webhook_message", return_value=None):
        response = client.post(
            "/api/v1/webhooks/whatsapp",
            content=body,
            headers={"X-Hub-Signature-256": signature, "Content-Type": "application/json"}
        )
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
