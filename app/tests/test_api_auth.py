import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app
from app.database import Base, engine

# Create tables for testing
Base.metadata.create_all(bind=engine)

client = TestClient(app)

def test_admin_api_misconfigured():
    """
    Test that admin endpoints return 500 if ADMIN_API_KEY is not set.
    """
    # Ensure settings.admin_api_key is empty (default)
    with patch("app.config.settings.admin_api_key", ""):
        response = client.get("/api/v1/members/")
        assert response.status_code == 500
        assert "Misconfiguration" in response.json()["detail"]

def test_admin_api_unauthorized_missing_header():
    """
    Test that admin endpoints return 401 if header is missing.
    """
    with patch("app.config.settings.admin_api_key", "test-secret-key"):
        response = client.get("/api/v1/members/")
        assert response.status_code == 401
        assert "Missing authentication header: X-Admin-Key" == response.json()["detail"]

def test_admin_api_unauthorized_invalid_key():
    """
    Test that admin endpoints return 401 if key is invalid.
    """
    with patch("app.config.settings.admin_api_key", "test-secret-key"):
        response = client.get("/api/v1/members/", headers={"X-Admin-Key": "wrong-key"})
        assert response.status_code == 401
        assert "Invalid Admin API Key" in response.json()["detail"]

def test_members_api_authorized():
    """
    Test that members API returns 200 with valid key.
    """
    with patch("app.config.settings.admin_api_key", "test-secret-key"):
        response = client.get(
            "/api/v1/members/",
            headers={"X-Admin-Key": "test-secret-key"}
        )
        assert response.status_code == 200

def test_classes_api_protected():
    """
    Test that classes API is protected.
    """
    with patch("app.config.settings.admin_api_key", "test-secret-key"):
        response = client.get(
            "/api/v1/classes/",
            headers={"X-Admin-Key": "wrong-key"}
        )
        assert response.status_code == 401

def test_chat_member_context_protected():
    """
    Test that sensitive chat endpoint is protected.
    """
    with patch("app.config.settings.admin_api_key", "test-secret-key"):
        response = client.get(
            "/api/v1/chat/member/1234567890",
            headers={"X-Admin-Key": "wrong-key"}
        )
        assert response.status_code == 401

def test_chat_message_public_access():
    """
    Test that standard chat message endpoint remains PUBLIC.
    """
    with patch("app.config.settings.admin_api_key", "test-secret-key"):
        # Should NOT return 401 Unauthorized
        response = client.post(
            "/api/v1/chat/message",
            json={"phone": "1234567890", "message": "hello"}
        )
        assert response.status_code != 401
        assert response.status_code != 403
