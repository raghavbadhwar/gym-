"""
Security Services
Handles cryptographic verification and security utilities.
"""
import hmac
import hashlib
from fastapi import Request, HTTPException, Header
from loguru import logger
from typing import Optional

from app.config import settings

async def validate_whatsapp_signature(
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256")
):
    """
    Validate the incoming payload from WhatsApp against the X-Hub-Signature-256 header.

    This middleware-like dependency ensures that requests actually come from Meta.
    It computes the HMAC-SHA256 of the request body using the App Secret and
    compares it with the signature provided in the header.

    If the App Secret is not configured, it logs a warning and allows the request
    (fail-open) to prevent breaking existing deployments, but this is insecure.
    """
    # 1. Check if verification is enabled (secret is configured)
    if not settings.whatsapp_app_secret:
        # In production, this should probably be an error, but for now we warn
        logger.warning("⚠️ WhatsApp App Secret not configured - skipping signature verification")
        return

    # 2. Check if signature header is present
    if not x_hub_signature_256:
        logger.warning("❌ Missing X-Hub-Signature-256 header on webhook request")
        raise HTTPException(status_code=403, detail="Missing signature header")

    try:
        # 3. Extract signature (format: sha256=<signature>)
        if not x_hub_signature_256.startswith("sha256="):
             logger.warning(f"❌ Invalid signature format: {x_hub_signature_256}")
             raise HTTPException(status_code=403, detail="Invalid signature format")

        signature = x_hub_signature_256.split("=")[1]

        # 4. Get raw body
        # request.body() is cached by Starlette/FastAPI, so it can be called multiple times
        body = await request.body()

        # 5. Calculate expected HMAC
        expected_signature = hmac.new(
            key=settings.whatsapp_app_secret.encode(),
            msg=body,
            digestmod=hashlib.sha256
        ).hexdigest()

        # 6. Compare securely (constant-time comparison)
        if not hmac.compare_digest(signature, expected_signature):
            logger.warning(f"❌ Signature mismatch! Expected: {expected_signature}, Got: {signature}")
            raise HTTPException(status_code=403, detail="Invalid signature")

        # If we get here, signature is valid
        # logger.debug("✅ Webhook signature verified")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error validating signature: {e}")
        raise HTTPException(status_code=403, detail="Signature validation error")
