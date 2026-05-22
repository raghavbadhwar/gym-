## 2026-02-20 - [WhatsApp Webhook Security Gap]
**Vulnerability:** The WhatsApp webhook endpoint (`/api/v1/webhooks/whatsapp`) accepted POST requests without validating the `X-Hub-Signature-256` header, allowing potential attackers to spoof messages from users and trigger actions on their behalf.
**Learning:** Third-party webhooks (like Meta/WhatsApp) require explicit signature verification. The lack of this check in the initial implementation meant the system relied solely on obscurity (the callback URL).
**Prevention:** Always implement signature verification middleware or dependencies for external webhooks immediately. Use `hmac.compare_digest` to prevent timing attacks.
