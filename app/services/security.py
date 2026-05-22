import hmac
import hashlib
from fastapi import Request, Header, HTTPException
from loguru import logger
from app.config import settings

async def validate_whatsapp_signature(request: Request, x_hub_signature_256: str = Header(None)):
    """
    Validate the WhatsApp webhook signature.

    Meta sends an X-Hub-Signature-256 header with the request.
    This is the HMAC-SHA256 of the request body using the App Secret.
    """
    if not settings.whatsapp_app_secret:
        logger.warning("⚠️ WhatsApp App Secret not configured - skipping signature verification")
        return

    if not x_hub_signature_256:
        logger.warning("🚫 Webhook request missing signature header")
        raise HTTPException(status_code=403, detail="Missing signature")

    # Extract signature (remove 'sha256=' prefix if present)
    expected_signature = x_hub_signature_256
    if expected_signature.startswith("sha256="):
        expected_signature = expected_signature[7:]

    # Read raw body
    body = await request.body()

    # Calculate signature
    calculated_signature = hmac.new(
        settings.whatsapp_app_secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    # Compare securely
    if not hmac.compare_digest(expected_signature, calculated_signature):
        logger.warning(f"🚫 Invalid webhook signature. Expected: {expected_signature}, Calculated: {calculated_signature}")
        raise HTTPException(status_code=403, detail="Invalid signature")

    logger.debug("✅ Webhook signature verified")
