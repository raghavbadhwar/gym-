## 2024-05-24 - Missing Webhook Signature Validation

**Vulnerability:** The WhatsApp webhook endpoint (`/whatsapp` POST) in `app/routers/webhooks.py` lacked `X-Hub-Signature-256` validation. This could allow an attacker to send unauthorized payloads, masquerading as Meta.
**Learning:** In webhook architectures, missing payload signature validation can result in unauthorized operations being executed. A fail-secure approach using `HTTPException` inside the catch-all `Exception` block ensures specific errors are appropriately propagated.
**Prevention:** Always implement HMAC SHA256 validation to authenticate incoming webhook payloads. Require an app secret (`whatsapp_app_secret`) in the app configuration, and use `hmac.compare_digest()` to compare signatures in a timing-attack resistant manner.
