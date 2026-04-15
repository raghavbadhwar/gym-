## 2024-05-18 - Missing Webhook Signature Validation
**Vulnerability:** The WhatsApp webhook endpoint (`/api/v1/webhooks/whatsapp`) accepts POST requests without validating the `X-Hub-Signature-256` header, allowing anyone to spoof messages to the bot.
**Learning:** Webhooks require strong authentication to ensure they come from the expected provider. Meta provides a signature header that must be validated using the `whatsapp_app_secret`.
**Prevention:** Always implement signature validation for webhooks using `hmac.compare_digest` to prevent spoofing and timing attacks.
