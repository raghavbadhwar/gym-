import hashlib
import hmac
from fastapi import Request, Header, HTTPException
from app.config import settings

async def validate_whatsapp_signature(request: Request, x_hub_signature_256: str = Header(None)):
    """
    Validates the WhatsApp webhook signature using HMAC-SHA256.

    If whatsapp_app_secret is not configured, validation is skipped (for backward compatibility).
    """
    if not settings.whatsapp_app_secret:
        return

    if not x_hub_signature_256:
        raise HTTPException(status_code=401, detail="Missing X-Hub-Signature-256 header")

    body = await request.body()

    # Calculate the HMAC-SHA256 signature
    signature = hmac.new(
        settings.whatsapp_app_secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    expected_signature = f"sha256={signature}"

    if not hmac.compare_digest(expected_signature, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid signature")
