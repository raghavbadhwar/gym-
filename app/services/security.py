import hmac
import hashlib
from fastapi import Request, Header, HTTPException, status
from loguru import logger
from app.config import settings

async def validate_whatsapp_signature(request: Request, x_hub_signature_256: str = Header(None)):
    """
    Validates the WhatsApp webhook signature.

    Args:
        request: The FastAPI request object
        x_hub_signature_256: The signature header from WhatsApp (sha256=...)
    """
    secret = settings.whatsapp_app_secret

    if not secret:
        logger.warning("⚠️ WHATSAPP_APP_SECRET is not set! Webhook signature verification is skipped.")
        return True

    if not x_hub_signature_256:
        logger.error("🛑 Missing X-Hub-Signature-256 header")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing signature header"
        )

    # Get the raw body
    body = await request.body()

    # Calculate the expected signature
    try:
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            body,
            hashlib.sha256
        ).hexdigest()

        received_signature = x_hub_signature_256.replace("sha256=", "")

        if not hmac.compare_digest(expected_signature, received_signature):
            logger.error(f"🛑 Invalid webhook signature. Received: {received_signature}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid signature"
            )

        logger.debug("✅ Webhook signature verified")
        return True

    except Exception as e:
        # Re-raise HTTP exceptions (like the one above)
        if isinstance(e, HTTPException):
            raise e

        logger.error(f"🛑 Error verifying signature: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Signature verification failed"
        )
