"""
Security Service
Handles request validation and signature verification for webhooks.
"""
import hmac
import hashlib
from fastapi import Request, HTTPException, status
from loguru import logger
from app.config import settings

async def validate_whatsapp_signature(request: Request):
    """
    Validates the X-Hub-Signature-256 header for WhatsApp webhooks.

    If whatsapp_app_secret is configured, this function verifies that the
    incoming request was signed by Meta using the app secret.

    Raises HTTPException(401) if signature is missing or invalid.
    """
    secret = settings.whatsapp_app_secret

    # If no secret is configured, we can't verify signatures.
    # Log a warning but allow the request to proceed (fail open for compatibility).
    if not secret:
        logger.warning("⚠️ WhatsApp App Secret not configured - skipping signature verification!")
        return

    # Get the signature from headers
    signature_header = request.headers.get("X-Hub-Signature-256")

    if not signature_header:
        logger.error("❌ Missing X-Hub-Signature-256 header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing signature header"
        )

    # Extract the signature hash (remove 'sha256=' prefix if present)
    # Meta sends: "sha256=<hash>"
    if signature_header.startswith("sha256="):
        signature_hash = signature_header[7:]
    else:
        signature_hash = signature_header

    try:
        # Read the raw body
        # request.body() is cached by FastAPI so it can be read again later
        body = await request.body()

        # Calculate expected signature
        expected_hash = hmac.new(
            key=secret.encode('utf-8'),
            msg=body,
            digestmod=hashlib.sha256
        ).hexdigest()

        # specific check using hmac.compare_digest to prevent timing attacks
        if not hmac.compare_digest(expected_hash, signature_hash):
            logger.error(f"❌ Invalid signature. Expected: {expected_hash}, Got: {signature_hash}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature"
            )

        # logger.debug("✅ Webhook signature verified successfully")

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"Error during signature verification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Signature verification failed"
        )
