"""
Security services for webhook verification and other security features.
"""
import hmac
import hashlib
from fastapi import Request, HTTPException, Header
from loguru import logger
from app.config import settings

async def validate_whatsapp_signature(
    request: Request,
    x_hub_signature_256: str = Header(None, alias="X-Hub-Signature-256")
):
    """
    Validate the WhatsApp webhook signature using HMAC-SHA256.

    Args:
        request: The incoming FastAPI request
        x_hub_signature_256: The signature header provided by Meta

    Raises:
        HTTPException(403): If signature is missing or invalid
    """
    # If secret is not set, log warning but allow (fail open to prevent breaking changes)
    # In a stricter environment, this should fail closed.
    if not settings.whatsapp_app_secret:
        logger.warning("⚠️ WHATSAPP_APP_SECRET not set - skipping signature verification")
        return

    if not x_hub_signature_256:
        logger.warning("⚠️ Missing X-Hub-Signature-256 header on webhook request")
        raise HTTPException(status_code=403, detail="Missing signature header")

    # Meta sends signature as "sha256=<signature>"
    signature = x_hub_signature_256
    if signature.startswith("sha256="):
        signature = signature[7:]

    # Get raw body bytes
    try:
        body = await request.body()
    except Exception as e:
        logger.error(f"Error reading request body for signature verification: {e}")
        raise HTTPException(status_code=500, detail="Error reading request body")

    # Calculate expected signature
    try:
        expected_signature = hmac.new(
            settings.whatsapp_app_secret.encode("utf-8"),
            msg=body,
            digestmod=hashlib.sha256
        ).hexdigest()
    except Exception as e:
        logger.error(f"Error calculating signature: {e}")
        raise HTTPException(status_code=500, detail="Error calculating signature")

    # Constant-time comparison to prevent timing attacks
    if not hmac.compare_digest(signature, expected_signature):
        logger.warning(f"❌ Invalid webhook signature! Expected: {expected_signature[:10]}..., Got: {signature[:10]}...")
        raise HTTPException(status_code=403, detail="Invalid signature")

    logger.debug("✅ Webhook signature verified")
