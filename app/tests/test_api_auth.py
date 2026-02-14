import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app

client = TestClient(app)

def test_api_auth_missing_header():
    # Patch the settings to ensure a key is configured
    with patch("app.auth.settings.admin_api_key", "secret-key"):
        # Without header
        response = client.get("/api/v1/members/")
        # Expect 422 because header is required
        assert response.status_code == 422

def test_api_auth_invalid_header():
    with patch("app.auth.settings.admin_api_key", "secret-key"):
        # With wrong header
        response = client.get("/api/v1/members/", headers={"X-Admin-Key": "wrong-key"})
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid Admin API Key"

def test_api_auth_valid_header():
    with patch("app.auth.settings.admin_api_key", "secret-key"):
        # Mock the MemberService to avoid DB calls
        with patch("app.routers.members.MemberService") as MockService:
            instance = MockService.return_value
            instance.search.return_value = []

            # With correct header
            response = client.get("/api/v1/members/", headers={"X-Admin-Key": "secret-key"})

            assert response.status_code == 200
            assert response.json() == {"count": 0, "members": []}

def test_api_auth_no_key_configured():
    # If settings.admin_api_key is empty (default), it should raise 500
    with patch("app.auth.settings.admin_api_key", ""):
        response = client.get("/api/v1/members/", headers={"X-Admin-Key": "any-key"})
        assert response.status_code == 500
        assert response.json()["detail"] == "Admin API Key not configured on server"
