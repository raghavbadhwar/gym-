import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from unittest.mock import patch

client = TestClient(app)

def test_members_endpoint_no_key_fails():
    """Accessing members endpoint without key should return 401."""
    # Mock settings to have a key configured
    with patch.object(settings, 'admin_api_key', 'test-secret-key'):
        response = client.get("/api/v1/members")
        assert response.status_code == 401
        assert response.json() == {"detail": "Missing API Key"}

def test_members_endpoint_invalid_key_fails():
    """Accessing members endpoint with invalid key should return 403."""
    with patch.object(settings, 'admin_api_key', 'test-secret-key'):
        response = client.get("/api/v1/members", headers={"X-Admin-Key": "wrong-key"})
        assert response.status_code == 403
        assert response.json() == {"detail": "Invalid API Key"}

def test_members_endpoint_valid_key_passes_auth():
    """Accessing members endpoint with valid key should pass auth (return 200)."""
    with patch.object(settings, 'admin_api_key', 'test-secret-key'):
        # Mock MemberService.search to return empty list and avoid DB call
        with patch("app.services.member_service.MemberService.search", return_value=[]):
            response = client.get("/api/v1/members", headers={"X-Admin-Key": "test-secret-key"})
            assert response.status_code == 200

def test_fail_secure_when_config_missing():
    """If admin_api_key is not configured (empty), endpoints should return 500."""
    # Mock settings to be empty
    with patch.object(settings, 'admin_api_key', ''):
        # Even with a key provided in header, it should fail 500
        response = client.get("/api/v1/members", headers={"X-Admin-Key": "some-key"})
        assert response.status_code == 500
        assert response.json() == {"detail": "Internal Server Error"}
