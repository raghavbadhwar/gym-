import unittest
from unittest.mock import patch
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.auth import get_admin_api_key

client = TestClient(app)

class TestAuth(unittest.TestCase):
    @patch("app.config.settings.admin_api_key", "valid_key")
    def test_get_admin_api_key_valid(self):
        """Test with a valid API key"""
        result = get_admin_api_key(api_key_header="valid_key")
        self.assertEqual(result, "valid_key")

    @patch("app.config.settings.admin_api_key", "valid_key")
    def test_get_admin_api_key_invalid(self):
        """Test with an invalid API key"""
        with self.assertRaises(HTTPException) as context:
            get_admin_api_key(api_key_header="invalid_key")
        self.assertEqual(context.exception.status_code, 403)
        self.assertEqual(context.exception.detail, "Could not validate credentials")

    @patch("app.config.settings.admin_api_key", "valid_key")
    def test_get_admin_api_key_missing(self):
        """Test with a missing API key header"""
        with self.assertRaises(HTTPException) as context:
            get_admin_api_key(api_key_header=None)
        self.assertEqual(context.exception.status_code, 403)
        self.assertEqual(context.exception.detail, "Could not validate credentials")

    @patch("app.config.settings.admin_api_key", "")
    def test_get_admin_api_key_missing_config(self):
        """Test when the server configuration is missing the API key"""
        with self.assertRaises(HTTPException) as context:
            get_admin_api_key(api_key_header="any_key")
        self.assertEqual(context.exception.status_code, 500)
        self.assertEqual(context.exception.detail, "Server configuration error: Admin API key not set")

if __name__ == "__main__":
    unittest.main()
