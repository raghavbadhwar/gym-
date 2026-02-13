import hashlib
import hmac
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db
from app.config import settings

client = TestClient(app)

# Override database dependency to avoid connection errors
def mock_get_db():
    try:
        db = MagicMock()
        yield db
    finally:
        pass

app.dependency_overrides[get_db] = mock_get_db

def test_webhook_no_signature_header_when_secret_set():
    with patch.object(settings, "whatsapp_app_secret", "test_secret"):
        response = client.post("/api/v1/webhooks/whatsapp", json={"test": "data"})
        assert response.status_code == 401
        assert response.json()["detail"] == "Missing X-Hub-Signature-256 header"

def test_webhook_invalid_signature_when_secret_set():
    with patch.object(settings, "whatsapp_app_secret", "test_secret"):
        body = '{"test": "data"}'
        response = client.post(
            "/api/v1/webhooks/whatsapp",
            content=body,
            headers={"X-Hub-Signature-256": "sha256=invalid", "Content-Type": "application/json"}
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid signature"

def test_webhook_valid_signature_when_secret_set():
    secret = "test_secret"
    body = '{"test": "data"}'
    signature = hmac.new(
        secret.encode(),
        body.encode(),
        hashlib.sha256
    ).hexdigest()

    with patch.object(settings, "whatsapp_app_secret", secret):
        # Mock internal service to return quickly
        with patch("app.routers.webhooks.whatsapp_service.parse_webhook_message") as mock_parse:
            mock_parse.return_value = None  # Simulate parsed message as None (status update)

            response = client.post(
                "/api/v1/webhooks/whatsapp",
                content=body,
                headers={"X-Hub-Signature-256": f"sha256={signature}", "Content-Type": "application/json"}
            )
            assert response.status_code == 200
            assert response.json() == {"status": "ok"}

def test_webhook_no_secret_configured_allows_request():
    with patch.object(settings, "whatsapp_app_secret", ""):
        with patch("app.routers.webhooks.whatsapp_service.parse_webhook_message") as mock_parse:
            mock_parse.return_value = None

            response = client.post("/api/v1/webhooks/whatsapp", json={"test": "data"})
            assert response.status_code == 200
