import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_webhook_verify_success():
    response = client.get("/api/v1/webhooks/whatsapp?hub.mode=subscribe&hub.verify_token=gymbuddy_verify_token_2026&hub.challenge=1234")
    assert response.status_code == 200
    assert response.text == "1234"

def test_webhook_verify_failure():
    response = client.get("/api/v1/webhooks/whatsapp?hub.mode=subscribe&hub.verify_token=wrong&hub.challenge=1234")
    assert response.status_code == 403

def test_test_send_unauthorized():
    # Only allowed in dev mode
    import app.routers.webhooks
    app.routers.webhooks.settings.app_env = "production"

    response = client.post("/api/v1/webhooks/test/send?phone=123&message=hi")
    assert response.status_code == 403

    app.routers.webhooks.settings.app_env = "development"

def test_webhook_post_missing_secret():
    import app.routers.webhooks
    original_secret = app.routers.webhooks.settings.whatsapp_app_secret
    app.routers.webhooks.settings.whatsapp_app_secret = ""

    response = client.post("/api/v1/webhooks/whatsapp", json={"test": "data"})
    assert response.status_code == 500

    app.routers.webhooks.settings.whatsapp_app_secret = original_secret

def test_webhook_post_missing_signature():
    import app.routers.webhooks
    app.routers.webhooks.settings.whatsapp_app_secret = "test_secret"

    response = client.post("/api/v1/webhooks/whatsapp", json={"test": "data"})
    assert response.status_code == 401

    app.routers.webhooks.settings.whatsapp_app_secret = ""

def test_webhook_post_invalid_signature():
    import app.routers.webhooks
    app.routers.webhooks.settings.whatsapp_app_secret = "test_secret"

    response = client.post(
        "/api/v1/webhooks/whatsapp",
        json={"test": "data"},
        headers={"X-Hub-Signature-256": "sha256=invalid"}
    )
    assert response.status_code == 401

    app.routers.webhooks.settings.whatsapp_app_secret = ""

def test_webhook_post_valid_signature():
    import app.routers.webhooks
    import hmac
    import hashlib
    import json

    app.routers.webhooks.settings.whatsapp_app_secret = "test_secret"

    payload = {"test": "data"}
    body_bytes = json.dumps(payload).replace(" ", "").encode('utf-8')

    signature = hmac.new(
        key=b"test_secret",
        msg=body_bytes,
        digestmod=hashlib.sha256
    ).hexdigest()

    response = client.post(
        "/api/v1/webhooks/whatsapp",
        content=body_bytes,
        headers={"X-Hub-Signature-256": f"sha256={signature}"}
    )

    # Because of missing mock for AI/Service, it returns 200 {"status": "ok"} when not a full message structure
    # as parse_webhook_message returns None, triggering early return {"status": "ok"}
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

    app.routers.webhooks.settings.whatsapp_app_secret = ""
