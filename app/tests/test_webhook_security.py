import unittest
from unittest.mock import patch, MagicMock
from app.services.security import validate_whatsapp_signature
from fastapi.testclient import TestClient
from app.main import app
import hmac
import hashlib
import json

class TestWebhookSecurity(unittest.TestCase):

    def test_validate_signature_valid(self):
        """Test validation with correct signature"""
        secret = "my_secret"
        payload = b'{"hello": "world"}'

        # Calculate valid signature
        signature = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        header = f"sha256={signature}"

        with patch("app.services.security.settings.whatsapp_app_secret", secret):
            result = validate_whatsapp_signature(payload, header)
            self.assertTrue(result)

    def test_validate_signature_invalid(self):
        """Test validation with incorrect signature"""
        secret = "my_secret"
        payload = b'{"hello": "world"}'
        header = "sha256=invalid_signature"

        with patch("app.services.security.settings.whatsapp_app_secret", secret):
            result = validate_whatsapp_signature(payload, header)
            self.assertFalse(result)

    def test_validate_signature_missing_header(self):
        """Test validation with missing header"""
        secret = "my_secret"
        payload = b'{"hello": "world"}'

        with patch("app.services.security.settings.whatsapp_app_secret", secret):
            result = validate_whatsapp_signature(payload, None)
            self.assertFalse(result)

    def test_validate_signature_no_secret_configured(self):
        """Test validation skipped when secret is not configured"""
        payload = b'{"hello": "world"}'
        header = "sha256=whatever"

        with patch("app.services.security.settings.whatsapp_app_secret", ""):
            result = validate_whatsapp_signature(payload, header)
            self.assertTrue(result)

    def test_webhook_endpoint_rejects_invalid_signature(self):
        """Test that the webhook endpoint rejects requests with invalid signatures"""
        client = TestClient(app)
        secret = "test_secret"
        payload = {"object": "whatsapp_business_account"}

        # Patch the settings in the security module where it is used
        with patch("app.services.security.settings.whatsapp_app_secret", secret):
            response = client.post(
                "/api/v1/webhooks/whatsapp",
                json=payload,
                headers={"X-Hub-Signature-256": "sha256=invalid"}
            )
            self.assertEqual(response.status_code, 403)
            self.assertEqual(response.json()["detail"], "Invalid signature")

    def test_webhook_endpoint_accepts_valid_signature(self):
        """Test that the webhook endpoint accepts requests with valid signatures"""
        client = TestClient(app)
        secret = "test_secret"
        payload_dict = {"object": "whatsapp_business_account"}
        payload_bytes = json.dumps(payload_dict).encode()

        signature = hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()
        header = f"sha256={signature}"

        # Patch settings
        with patch("app.services.security.settings.whatsapp_app_secret", secret):
            # Patch whatsapp_service to avoid side effects
            with patch("app.routers.webhooks.whatsapp_service.parse_webhook_message", return_value=None):
                 response = client.post(
                    "/api/v1/webhooks/whatsapp",
                    content=payload_bytes,
                    headers={"X-Hub-Signature-256": header, "Content-Type": "application/json"}
                )
                 self.assertEqual(response.status_code, 200)
