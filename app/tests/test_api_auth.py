"""
Test API Authentication
Verifies that administrative endpoints are protected by the API Key.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app

# Use TestClient with the actual app
client = TestClient(app)

def test_members_endpoint_misconfiguration():
    """Verify that members endpoint returns 500 if server has no key configured."""
    # We patch the instance attribute on the already imported settings object in config
    with patch("app.config.settings.admin_api_key", ""):
        # We must send a header to bypass the auto_error=True check of APIKeyHeader
        response = client.get("/api/v1/members/", headers={"X-Admin-Key": "any-key"})
        assert response.status_code == 500
        assert "Server Misconfiguration" in response.json()["detail"]

def test_members_endpoint_missing_header():
    """Verify that members endpoint returns 403 if header is missing."""
    with patch("app.config.settings.admin_api_key", "secret-key"):
        response = client.get("/api/v1/members/")
        assert response.status_code == 403
        assert response.json()["detail"] == "Not authenticated"

def test_members_endpoint_invalid_key():
    """Verify that members endpoint returns 401 if key is invalid."""
    with patch("app.config.settings.admin_api_key", "secret-key"):
        response = client.get("/api/v1/members/", headers={"X-Admin-Key": "wrong-key"})
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid Admin API Key"

def test_members_endpoint_success():
    """Verify that access is granted with correct key."""
    # We patch MemberService.search to avoid DB interaction issues
    # and settings.database_url just in case
    with patch("app.config.settings.admin_api_key", "secret-key"), \
         patch("app.services.member_service.MemberService.search", return_value=[]):

        response = client.get("/api/v1/members/", headers={"X-Admin-Key": "secret-key"})
        assert response.status_code == 200
        assert response.json()["members"] == []

def test_classes_endpoint_protected():
    """Verify classes endpoint is also protected."""
    with patch("app.config.settings.admin_api_key", "secret-key"):
        response = client.get("/api/v1/classes/", headers={"X-Admin-Key": "wrong-key"})
        assert response.status_code == 401
