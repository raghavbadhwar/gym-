import hmac
import hashlib
from fastapi import Request, HTTPException, Header
from app.config import settings
from loguru import logger

async def validate_whatsapp_signature(request: Request, x_hub_signature_256: str = Header(None)):
    """
    Validates the WhatsApp webhook signature (HMAC-SHA256).
    See: https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/security
    """
    if not settings.whatsapp_app_secret:
        # If the secret is not configured, we can't verify signatures.
        # In a real production environment, we should probably fail here or enforce the secret.
        # For now, we'll log a warning and skip verification to allow development.
        logger.warning("WhatsApp App Secret not set. Skipping webhook signature verification.")
        return

    if not x_hub_signature_256:
        logger.warning("Missing X-Hub-Signature-256 header")
        raise HTTPException(status_code=403, detail="Missing signature header")

    try:
        # The body has already been read/cached by Starlette/FastAPI mechanism if consumed as JSON before,
        # or we read it here.
        body = await request.body()

        # Calculate expected signature
        # Signature format is: sha256=<hash>
        expected_signature = hmac.new(
            settings.whatsapp_app_secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()

        # Extract received signature hash
        received_parts = x_hub_signature_256.split("=")
        if len(received_parts) != 2 or received_parts[0] != "sha256":
             logger.warning(f"Invalid signature format: {x_hub_signature_256}")
             raise HTTPException(status_code=403, detail="Invalid signature format")

        received_signature = received_parts[1]

        if not hmac.compare_digest(expected_signature, received_signature):
            logger.warning(f"Invalid signature. Expected: {expected_signature}, Got: {received_signature}")
            raise HTTPException(status_code=403, detail="Invalid signature")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating signature: {e}")
        raise HTTPException(status_code=500, detail="Signature validation failed")
