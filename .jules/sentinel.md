## 2026-03-28 - Missing Webhook Signature Validation

**Vulnerability:** Meta WhatsApp webhook endpoints (`/api/v1/webhooks/whatsapp` POST) were missing `X-Hub-Signature-256` signature validation. This allowed an attacker to potentially forge incoming messages and commands.
**Learning:** External webhook requests must have cryptographically verifiable signatures. Also, explicitly catching and re-raising `HTTPException` inside of broad `Exception` handlers is critical to ensuring Fail-Secure behavior (returning a 401 or 500 status code) instead of gracefully returning 200 OK to malicious requests.
**Prevention:** Always use `hmac.compare_digest` to prevent timing attacks. Enforce fail-secure configurations where missing secrets return an HTTP 500 rather than bypassing the check.
