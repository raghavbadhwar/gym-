"""
Security Service
Handles authentication and signature verification for external integrations.
"""
import hmac
import hashlib
from fastapi import Request, HTTPException, Header
from loguru import logger
from app.config import settings

async def validate_whatsapp_signature(
    request: Request,
    x_hub_signature_256: str | None = Header(None, alias="X-Hub-Signature-256")
):
    """
    Validate the X-Hub-Signature-256 header from WhatsApp Webhooks.

    If whatsapp_app_secret is not configured, verification is skipped (development mode).
    Otherwise, it computes the HMAC-SHA256 of the request body and compares it.
    """
    if not settings.whatsapp_app_secret:
        # In development/demo, we might not have this configured yet
        # logger.warning("⚠️ WhatsApp App Secret not configured - skipping signature verification")
        return

    if not x_hub_signature_256:
        logger.warning("⚠️ Missing X-Hub-Signature-256 header")
        raise HTTPException(status_code=401, detail="Missing signature header")

    # Get raw body
    body = await request.body()

    # Extract signature (format: sha256=hash)
    signature = x_hub_signature_256.replace("sha256=", "")

    # Compute expected signature
    expected_signature = hmac.new(
        settings.whatsapp_app_secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    # Compare safely
    if not hmac.compare_digest(signature, expected_signature):
        logger.warning(f"❌ Invalid signature! Expected: {expected_signature}, Got: {signature}")
        raise HTTPException(status_code=403, detail="Invalid signature")
