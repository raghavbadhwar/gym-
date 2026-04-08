## 2025-04-08 - Fix Missing Webhook Signature Verification
**Vulnerability:** The WhatsApp webhook endpoint was accepting any payload without verifying its authenticity, exposing the system to unauthorized data injection or spam.
**Learning:** Always verify incoming webhooks using HMAC signatures (like `X-Hub-Signature-256` for Meta). Ensure that any security failure correctly raises an HTTP exception instead of returning a 200 OK.
**Prevention:** Implement signature validation using `hmac.compare_digest` securely, and handle exceptions correctly in FastAPI routes.
