import pytest
import hmac
import hashlib
import json
from fastapi.testclient import TestClient

from app.main import app
from app.config import Settings
import app.routers.webhooks as webhooks

client = TestClient(app)

class MockSettings(Settings):
    whatsapp_app_secret: str = "test_secret_key"
    openai_api_key: str = "fake_key"

@pytest.fixture
def mock_settings(monkeypatch):
    settings = MockSettings()
    monkeypatch.setattr(webhooks, "settings", settings)
    return settings

def test_missing_app_secret(monkeypatch):
    class NoSecretSettings(Settings):
        whatsapp_app_secret: str = ""
        openai_api_key: str = "fake"
    monkeypatch.setattr(webhooks, "settings", NoSecretSettings())

    response = client.post("/api/v1/webhooks/whatsapp", json={"test": "data"})
    assert response.status_code == 500
    assert "Server configuration error" in response.json()["detail"]

def test_missing_signature(mock_settings):
    response = client.post("/api/v1/webhooks/whatsapp", json={"test": "data"})
    assert response.status_code == 401
    assert "Missing signature" in response.json()["detail"]

def test_invalid_signature(mock_settings):
    headers = {
        "x-hub-signature-256": "sha256=invalid_hash_value"
    }
    response = client.post("/api/v1/webhooks/whatsapp", json={"test": "data"}, headers=headers)
    assert response.status_code == 401
    assert "Invalid signature" in response.json()["detail"]

def test_valid_signature(mock_settings):
    payload = {"test": "data"}
    raw_body = json.dumps(payload).replace(" ", "").encode("utf-8")

    # Fast api test client json dumps differently, we need to send raw bytes to get the signature right
    raw_body = b'{"test":"data"}'

    signature = hmac.new(
        mock_settings.whatsapp_app_secret.encode("utf-8"),
        raw_body,
        hashlib.sha256
    ).hexdigest()

    headers = {
        "x-hub-signature-256": f"sha256={signature}",
        "Content-Type": "application/json"
    }

    response = client.post("/api/v1/webhooks/whatsapp", content=raw_body, headers=headers)
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
