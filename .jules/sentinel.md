## 2025-03-06 - [Missing Webhook Authentication]
**Vulnerability:** The `/api/v1/webhooks/whatsapp` POST endpoint was missing authentication, allowing any malicious actor to send fake WhatsApp messages and trigger application logic or AI interactions by spoofing requests to the webhook URL.
**Learning:** External webhooks (especially ones executing state-changing logic or AI generation) must always verify the incoming payload signature against a shared secret to ensure authenticity and integrity.
**Prevention:** Always implement `X-Hub-Signature-256` HMAC-SHA256 verification (using `hmac.compare_digest` to prevent timing attacks) on webhook endpoints before processing the request body.
