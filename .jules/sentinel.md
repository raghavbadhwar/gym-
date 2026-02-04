## 2024-05-23 - Webhook Signature Verification Gap
**Vulnerability:** The WhatsApp webhook endpoint (`/api/v1/webhooks/whatsapp`) accepted POST requests without verifying the `X-Hub-Signature-256` header, allowing potential attackers to inject fake messages.
**Learning:** Developers often assume obscure webhook URLs are secret enough or forget verification when focusing on functionality. Dependencies on external services (Meta) require strict ingress validation.
**Prevention:** Enforce `validate_whatsapp_signature` dependency on all webhook endpoints receiving external data. Use `hmac.compare_digest` to prevent timing attacks.
