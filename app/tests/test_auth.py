from fastapi.testclient import TestClient
from unittest.mock import patch
import pytest

from app.main import app
from app.config import settings

client = TestClient(app)

def test_admin_auth_fail_secure_missing_config():
    """
    FAIL SECURE: If admin_api_key is not configured (empty string),
    the application should raise 500 and block access.
    """
    # Patch the settings object instance attribute directly
    with patch.object(settings, "admin_api_key", ""):
        # We need to reload the app or ensure the dependency sees the change?
        # Since get_admin_api_key accesses settings.admin_api_key at runtime, patching the instance should work.

        response = client.get("/api/v1/members/")
        assert response.status_code == 500
        assert "Internal Server Error" in response.text

def test_admin_auth_missing_header():
    """
    If configured, but header is missing, return 403.
    """
    with patch.object(settings, "admin_api_key", "test-secret-key"):
        response = client.get("/api/v1/members/")
        assert response.status_code == 403
        assert "Could not validate credentials" in response.json()["detail"]

def test_admin_auth_invalid_key():
    """
    If configured, but key is wrong, return 403.
    """
    with patch.object(settings, "admin_api_key", "test-secret-key"):
        response = client.get(
            "/api/v1/members/",
            headers={"X-Admin-API-Key": "wrong-key"}
        )
        assert response.status_code == 403

def test_admin_auth_success():
    """
    If configured and key is correct, allow access.
    """
    with patch.object(settings, "admin_api_key", "test-secret-key"):
        # Mock MemberService to avoid DB errors
        with patch("app.routers.members.MemberService") as MockService:
            mock_instance = MockService.return_value
            mock_instance.search.return_value = []

            response = client.get(
                "/api/v1/members/",
                headers={"X-Admin-API-Key": "test-secret-key"}
            )
            assert response.status_code == 200

def test_classes_protected():
    """Verify classes endpoint is also protected."""
    with patch.object(settings, "admin_api_key", "test-secret-key"):
        response = client.get("/api/v1/classes/")
        assert response.status_code == 403

def test_chat_member_context_protected():
    """Verify chat sensitive endpoint is protected."""
    with patch.object(settings, "admin_api_key", "test-secret-key"):
        response = client.get("/api/v1/chat/member/+1234567890")
        assert response.status_code == 403
