import hmac
import hashlib
from fastapi import Request, Header, HTTPException, status
from loguru import logger
from app.config import settings

async def validate_whatsapp_signature(
    request: Request,
    x_hub_signature_256: str = Header(None)
):
    """
    Validate the incoming payload using HMAC-SHA256 signature.

    See: https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/security
    """

    # If no secret is configured, we can't verify (e.g. dev mode without secrets)
    if not settings.whatsapp_app_secret:
        logger.warning("⚠️ WhatsApp App Secret not configured - skipping signature verification")
        return

    if not x_hub_signature_256:
        logger.warning("🚫 Missing X-Hub-Signature-256 header")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing signature header"
        )

    # Extract the hash from "sha256=<hash>"
    parts = x_hub_signature_256.split("=")
    if len(parts) != 2 or parts[0] != "sha256":
        logger.warning("🚫 Invalid signature format")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid signature format"
        )

    signature_hash = parts[1]

    # Get the raw body
    body = await request.body()

    # Calculate expected HMAC
    expected_hash = hmac.new(
        settings.whatsapp_app_secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    # Compare
    if not hmac.compare_digest(expected_hash, signature_hash):
        logger.warning(f"🚫 Signature mismatch! Expected: {expected_hash}, Got: {signature_hash}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid signature"
        )

    logger.debug("✅ Webhook signature verified")
