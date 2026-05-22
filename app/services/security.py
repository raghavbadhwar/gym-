"""
Security Service - Handling authentication and signature verification
"""
import hmac
import hashlib
from fastapi import Request, HTTPException, Header
from loguru import logger
from app.config import settings

async def validate_whatsapp_signature(request: Request, x_hub_signature_256: str = Header(None)):
    """
    Validate the WhatsApp webhook signature using HMAC-SHA256.

    This ensures that the request is genuinely from Meta and not a spoofed request.

    Args:
        request: The FastAPI request object
        x_hub_signature_256: The signature header sent by Meta (automatically extracted)

    Raises:
        HTTPException(403): If the signature is missing or invalid
    """
    # If no secret is configured, strictly fail secure or warn depending on policy.
    # We will warn if missing but for security we should really enforce it.
    if not settings.whatsapp_app_secret:
        logger.warning("⚠️ WHATSAPP_APP_SECRET not configured! Webhook signature verification skipped.")
        return

    if not x_hub_signature_256:
        logger.error("🛑 Missing X-Hub-Signature-256 header")
        raise HTTPException(status_code=403, detail="Missing signature header")

    # The header comes as "sha256=<signature>"
    parts = x_hub_signature_256.split("=")
    if len(parts) != 2 or parts[0] != "sha256":
        logger.error(f"🛑 Invalid signature format: {x_hub_signature_256}")
        raise HTTPException(status_code=403, detail="Invalid signature format")

    signature = parts[1]

    # Read the raw body
    # Note: request.body() is cached by Starlette, so it can be read multiple times
    body = await request.body()

    # Calculate expected signature
    expected_signature = hmac.new(
        settings.whatsapp_app_secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    # Compare signatures using constant-time comparison
    if not hmac.compare_digest(expected_signature, signature):
        logger.error(f"🛑 Invalid signature! Expected: {expected_signature}, Got: {signature}")
        raise HTTPException(status_code=403, detail="Invalid signature")

    logger.debug("✅ Webhook signature verified")
