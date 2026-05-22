from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

def test_members_unauthorized():
    with TestClient(app) as client:
        response = client.get("/api/v1/members/")
        assert response.status_code == 403
        assert response.json() == {"detail": "Not authenticated"}

def test_members_invalid_key():
    with TestClient(app) as client:
        response = client.get("/api/v1/members/", headers={"X-Admin-API-Key": "wrong-key"})
        assert response.status_code == 403
        assert response.json() == {"detail": "Could not validate credentials"}

def test_members_valid_key():
    with TestClient(app) as client:
        response = client.get(
            "/api/v1/members/",
            headers={"X-Admin-API-Key": settings.admin_api_key}
        )
        # It might be 200 or 500 depending on DB state, but it should NOT be 403
        # Since we use in-memory sqlite for tests usually, or whatever settings defaults to.
        # If the endpoint works, it returns 200.
        assert response.status_code == 200

def test_classes_unauthorized():
    with TestClient(app) as client:
        response = client.get("/api/v1/classes/")
        assert response.status_code == 403

def test_classes_valid_key():
    with TestClient(app) as client:
        response = client.get(
            "/api/v1/classes/",
            headers={"X-Admin-API-Key": settings.admin_api_key}
        )
        assert response.status_code == 200
