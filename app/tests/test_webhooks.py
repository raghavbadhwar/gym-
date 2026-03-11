import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app

client = TestClient(app)

def test_verify_webhook_success():
    # settings.whatsapp_verify_token defaults to "gymbuddy_verify_token_2026"
    response = client.get(
        "/api/v1/webhooks/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "gymbuddy_verify_token_2026",
            "hub.challenge": "1158201444"
        }
    )
    assert response.status_code == 200
    assert response.text == "1158201444"

def test_verify_webhook_invalid_token():
    response = client.get(
        "/api/v1/webhooks/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong_token",
            "hub.challenge": "1158201444"
        }
    )
    assert response.status_code == 403
    assert response.json() == {"detail": "Verification failed - Invalid token"}

def test_verify_webhook_missing_token():
    response = client.get(
        "/api/v1/webhooks/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.challenge": "1158201444"
        }
    )
    assert response.status_code == 403
    assert response.json() == {"detail": "Verification failed - Invalid token"}

def test_verify_webhook_wrong_mode():
    response = client.get(
        "/api/v1/webhooks/whatsapp",
        params={
            "hub.mode": "other_mode",
            "hub.verify_token": "gymbuddy_verify_token_2026",
            "hub.challenge": "1158201444"
        }
    )
    assert response.status_code == 403
    assert response.json() == {"detail": "Verification failed - Invalid token"}
