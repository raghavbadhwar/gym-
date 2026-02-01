from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

def test_members_auth_missing():
    """Verify that members endpoints require auth."""
    with TestClient(app) as client:
        # Try to access list members without key
        response = client.get("/api/v1/members/")
        assert response.status_code == 401
        assert response.json() == {"detail": "Invalid or missing Admin API Key"}

        # Try to access stats
        response = client.get("/api/v1/members/stats/overview")
        assert response.status_code == 401

def test_members_auth_invalid():
    """Verify that members endpoints reject invalid keys."""
    with TestClient(app) as client:
        headers = {"X-Admin-API-Key": "wrong-key"}
        response = client.get("/api/v1/members/", headers=headers)
        assert response.status_code == 401

def test_members_auth_success():
    """Verify that members endpoints accept valid key."""
    with TestClient(app) as client:
        headers = {"X-Admin-API-Key": settings.admin_api_key}
        response = client.get("/api/v1/members/", headers=headers)
        assert response.status_code == 200

def test_classes_protected_endpoints():
    """Verify that sensitive class endpoints require auth."""
    with TestClient(app) as client:
        # Create class without key
        class_data = {
            "name": "Security Test Class",
            "class_type": "yoga",
            "trainer_name": "Sentinel",
            "scheduled_at": "2025-01-01T10:00:00",
            "duration_mins": 60
        }

        # No key
        response = client.post("/api/v1/classes/", json=class_data)
        assert response.status_code == 401

        # Valid key
        headers = {"X-Admin-API-Key": settings.admin_api_key}
        response = client.post("/api/v1/classes/", json=class_data, headers=headers)
        assert response.status_code == 201

def test_classes_public_endpoints():
    """Verify that reading classes is still public."""
    with TestClient(app) as client:
        response = client.get("/api/v1/classes/")
        assert response.status_code == 200
