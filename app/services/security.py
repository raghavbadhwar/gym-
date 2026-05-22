import hmac
import hashlib
from loguru import logger
from app.config import settings

def validate_whatsapp_signature(payload: bytes, signature: str) -> bool:
    """
    Validates the X-Hub-Signature-256 header from WhatsApp/Meta.

    Args:
        payload: Raw request body bytes
        signature: The signature header string (e.g., "sha256=...")

    Returns:
        bool: True if signature is valid or verification skipped, False otherwise
    """
    if not settings.whatsapp_app_secret:
        logger.warning("⚠️ WhatsApp App Secret not configured - skipping signature verification")
        return True

    if not signature:
        logger.warning("⚠️ Missing X-Hub-Signature-256 header")
        return False

    try:
        # Extract the signature hash (remove "sha256=" prefix)
        # The header format is "sha256=<signature>"
        parts = signature.split("=")
        if len(parts) != 2 or parts[0] != "sha256":
            logger.warning(f"⚠️ Invalid signature format: {signature}")
            return False

        expected_signature = parts[1]

        # Calculate HMAC-SHA256
        calculated_signature = hmac.new(
            settings.whatsapp_app_secret.encode("utf-8"),
            payload,
            hashlib.sha256
        ).hexdigest()

        # Compare safely to prevent timing attacks
        is_valid = hmac.compare_digest(expected_signature, calculated_signature)

        if not is_valid:
            logger.warning(f"❌ Signature verification failed!")

        return is_valid

    except Exception as e:
        logger.error(f"Error validating signature: {e}")
        return False
