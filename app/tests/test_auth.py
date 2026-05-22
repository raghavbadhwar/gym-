import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Import app modules
from app.routers import members_router
from app.config import settings
from app.database import get_db

# Create a test app
app = FastAPI()
app.include_router(members_router)

client = TestClient(app)

def test_auth_missing_header():
    """Test that request without X-Admin-Key header fails with 422"""
    # Override settings to simulate configured key
    with patch.object(settings, 'admin_api_key', 'secret123'):
        response = client.get("/api/v1/members/stats/overview")
        assert response.status_code == 422

def test_auth_invalid_key():
    """Test that request with wrong X-Admin-Key header fails with 401"""
    with patch.object(settings, 'admin_api_key', 'secret123'):
        response = client.get(
            "/api/v1/members/stats/overview",
            headers={"X-Admin-Key": "wrong-key"}
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid Admin API Key"

def test_auth_server_misconfigured():
    """Test that request fails with 500 if server has no admin key configured"""
    # Ensure admin_api_key is empty (as default)
    with patch.object(settings, 'admin_api_key', ''):
        # We need to provide *some* key to pass the 422 check for missing header
        response = client.get(
            "/api/v1/members/stats/overview",
            headers={"X-Admin-Key": "anything"}
        )
        assert response.status_code == 500
        assert response.json()["detail"] == "Internal Server Error"

def test_auth_valid_key():
    """Test that request with correct X-Admin-Key header passes auth check"""
    # Mock dependencies

    # 1. Mock DB session (dependency override)
    app.dependency_overrides[get_db] = lambda: MagicMock()

    # 2. Mock MemberService to avoid actual logic execution
    # We patch where it is imported in the router file
    with patch("app.routers.members.MemberService") as MockService:
        # Setup the mock return value for get_stats
        mock_instance = MockService.return_value
        mock_instance.get_stats.return_value = {"total": 100, "active": 50}

        with patch.object(settings, 'admin_api_key', 'secret123'):
            response = client.get(
                "/api/v1/members/stats/overview",
                headers={"X-Admin-Key": "secret123"}
            )

            # Reset dependency override
            app.dependency_overrides = {}

            assert response.status_code == 200
            assert response.json() == {"total": 100, "active": 50}
