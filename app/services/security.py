import hmac
import hashlib
import secrets
from fastapi import Request, HTTPException
from loguru import logger
from app.config import settings

async def validate_whatsapp_signature(request: Request):
    """
    Validates the X-Hub-Signature-256 header for WhatsApp Webhooks.

    This prevents attackers from sending fake webhook events.
    The signature is an HMAC-SHA256 hash of the request body using the App Secret.
    """
    if not settings.whatsapp_app_secret:
        # Log a warning if secret is missing but allow request (e.g. for dev convenience)
        # In a strict production environment, this should probably raise an error.
        logger.warning("⚠️ WhatsApp App Secret not configured - skipping signature verification!")
        return

    signature = request.headers.get("X-Hub-Signature-256")
    if not signature:
        logger.warning("Missing X-Hub-Signature-256 header")
        raise HTTPException(status_code=403, detail="Missing signature header")

    # Extract hash from "sha256=<hash>"
    if not signature.startswith("sha256="):
        logger.warning(f"Invalid signature format: {signature}")
        raise HTTPException(status_code=403, detail="Invalid signature format")

    expected_hash = signature[7:] # Remove "sha256=" prefix

    # Get raw body bytes
    try:
        body = await request.body()
    except Exception as e:
        logger.error(f"Failed to read request body: {e}")
        raise HTTPException(status_code=500, detail="Could not read request body")

    # Calculate HMAC
    # The key must be bytes
    secret_bytes = settings.whatsapp_app_secret.encode('utf-8')
    calculated_hmac = hmac.new(secret_bytes, body, hashlib.sha256).hexdigest()

    # Compare securely (prevent timing attacks)
    if not secrets.compare_digest(expected_hash, calculated_hmac):
        logger.warning(f"Signature verification failed! Expected: {expected_hash}, Got: {calculated_hmac}")
        raise HTTPException(status_code=403, detail="Invalid signature")

    logger.debug("Webhook signature verified successfully ✅")
