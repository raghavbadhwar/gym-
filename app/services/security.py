import hmac
import hashlib
from fastapi import Request, HTTPException
from loguru import logger
from app.config import settings

async def validate_whatsapp_signature(request: Request):
    """
    Validate the incoming webhook request signature from WhatsApp.

    This verifies that the request actually came from Meta/WhatsApp
    by checking the X-Hub-Signature-256 header against the app secret.
    """
    if not settings.whatsapp_app_secret:
        # If no secret is configured, skip validation (development mode)
        logger.warning("WhatsApp App Secret not configured - skipping signature validation")
        return

    # Meta sends the signature in the X-Hub-Signature-256 header
    signature_header = request.headers.get("x-hub-signature-256", "")

    if not signature_header or not signature_header.startswith("sha256="):
        logger.warning("Missing or invalid X-Hub-Signature-256 header")
        raise HTTPException(status_code=403, detail="Missing or invalid signature")

    # The signature from the header
    expected_signature = signature_header[7:]

    # Get the raw request body
    body = await request.body()

    # Calculate our own signature
    computed_signature = hmac.new(
        settings.whatsapp_app_secret.encode("utf-8"),
        msg=body,
        digestmod=hashlib.sha256
    ).hexdigest()

    # Compare signatures using a timing-attack resistant comparison
    if not hmac.compare_digest(expected_signature, computed_signature):
        logger.warning("WhatsApp webhook signature validation failed")
        raise HTTPException(status_code=403, detail="Invalid signature")

    logger.debug("WhatsApp signature validated successfully")
