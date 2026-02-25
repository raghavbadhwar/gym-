## 2025-05-15 - Missing Webhook Signature Verification
**Vulnerability:** The WhatsApp webhook endpoint (`/api/v1/webhooks/whatsapp`) was accepting POST requests without verifying the `X-Hub-Signature-256` header, allowing potential attackers to spoof messages from Meta.
**Learning:** External webhooks (like WhatsApp, Stripe) often provide cryptographic signatures that MUST be verified. Relying only on the initial GET verification token is insufficient for securing the data stream.
**Prevention:** Always implement signature verification middleware/dependency for webhook endpoints. Added `validate_whatsapp_signature` dependency using `hmac` and `secrets.compare_digest`.
