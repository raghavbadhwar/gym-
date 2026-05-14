"""
Security Service
Handles security-related functionality like signature verification.
"""
import hmac
import hashlib
import secrets
from fastapi import Request, HTTPException
from loguru import logger

async def validate_whatsapp_signature(request: Request, secret: str):
    """
    Validates the X-Hub-Signature-256 header from WhatsApp/Meta.

    Args:
        request: The incoming FastAPI request
        secret: The WhatsApp App Secret

    Raises:
        HTTPException(403): If signature is invalid or missing when secret is configured.
    """
    if not secret:
        logger.warning("⚠️ WhatsApp App Secret not configured! Skipping signature verification.")
        logger.warning("   Please set WHATSAPP_APP_SECRET in your .env file for security.")
        return

    signature_header = request.headers.get("X-Hub-Signature-256")

    if not signature_header:
        logger.warning("❌ Missing X-Hub-Signature-256 header")
        raise HTTPException(status_code=403, detail="Missing signature header")

    # Header format is "sha256=<signature>"
    if not signature_header.startswith("sha256="):
        logger.warning("❌ Invalid signature format")
        raise HTTPException(status_code=403, detail="Invalid signature format")

    expected_signature = signature_header[7:] # Remove "sha256=" prefix

    # Read the raw body
    # Note: request.body() is cached by Starlette, so it's safe to call multiple times
    body = await request.body()

    # Calculate HMAC-SHA256
    calculated_signature = hmac.new(
        key=secret.encode("utf-8"),
        msg=body,
        digestmod=hashlib.sha256
    ).hexdigest()

    # specific verification using constant-time comparison
    if not secrets.compare_digest(expected_signature, calculated_signature):
        logger.warning(f"❌ Signature verification failed!")
        logger.debug(f"Expected: {expected_signature}")
        logger.debug(f"Calculated: {calculated_signature}")
        raise HTTPException(status_code=403, detail="Invalid signature")

    logger.debug("✅ Webhook signature verified successfully")
