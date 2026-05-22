from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

def test_auth_flows():
    # Use context manager to trigger startup events (create tables)
    with TestClient(app) as client:
        # 1. Unauthorized Access
        response = client.get("/api/v1/members/")
        assert response.status_code == 403
        assert response.json() == {"detail": "Missing API Key"}

        # 2. Invalid Key Access
        response = client.get("/api/v1/members/", headers={"X-Admin-Key": "wrong-key"})
        assert response.status_code == 403
        assert response.json() == {"detail": "Invalid API Key"}

        # 3. Authorized Access
        response = client.get(
            "/api/v1/members/",
            headers={"X-Admin-Key": settings.admin_api_key}
        )
        # It might return 200 with empty list, or 500 if DB has issues,
        # but definitely NOT 403 if auth works.
        assert response.status_code == 200
        assert "members" in response.json()

        # 4. Public Endpoint Check (Chat)
        # This endpoint attempts to look up a member.
        # If DB tables exist (via lifespan), it should process or fail validation, but NOT 403.
        response = client.post(
            "/api/v1/chat/message",
            json={"phone": "123", "message": "hi"}
        )
        assert response.status_code != 403
