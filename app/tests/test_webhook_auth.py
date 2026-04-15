import pytest
from fastapi.testclient import TestClient
import hmac
import hashlib
import json
from unittest.mock import patch
from app.main import app

client = TestClient(app)

@patch('app.routers.webhooks.settings.whatsapp_app_secret', 'test_secret', create=True)
def test_webhook_signature():
    payload = {"test": "data"}
    payload_bytes = json.dumps(payload).encode('utf-8')

    # Calculate valid signature
    signature = "sha256=" + hmac.new(
        b"test_secret",
        payload_bytes,
        hashlib.sha256
    ).hexdigest()

    # Valid request
    response = client.post(
        "/api/v1/webhooks/whatsapp",
        json=payload,
        headers={"X-Hub-Signature-256": signature}
    )
    print("Valid sig response:", response.status_code)

if __name__ == "__main__":
    test_webhook_signature()
