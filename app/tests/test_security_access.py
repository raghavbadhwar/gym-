from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

def test_members_missing_key():
    with TestClient(app) as client:
        response = client.get("/api/v1/members/")
        assert response.status_code == 403
        assert response.json() == {"detail": "Not authenticated"}

def test_members_invalid_key():
    with TestClient(app) as client:
        response = client.get("/api/v1/members/", headers={"X-API-Key": "wrong-key"})
        assert response.status_code == 401
        assert response.json() == {"detail": "Invalid API Key"}

def test_members_valid_key():
    with TestClient(app) as client:
        response = client.get("/api/v1/members/", headers={"X-API-Key": settings.api_key})
        # If DB is initialized by lifespan, this should be 200
        assert response.status_code == 200

def test_classes_missing_key():
    with TestClient(app) as client:
        response = client.get("/api/v1/classes/")
        assert response.status_code == 403

def test_chat_missing_key():
    with TestClient(app) as client:
        response = client.post("/api/v1/chat/message", json={"phone": "123", "message": "hi"})
        assert response.status_code == 403

def test_webhooks_public():
    with TestClient(app) as client:
        # Webhooks should NOT require the X-API-Key header
        response = client.get("/api/v1/webhooks/whatsapp?hub.mode=subscribe&hub.verify_token=wrong&hub.challenge=123")
        assert response.status_code == 403
        assert response.json() == {"detail": "Verification failed - Invalid token"}
