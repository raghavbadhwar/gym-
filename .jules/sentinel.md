## 2025-05-21 - Webhook Signature Bypass
**Vulnerability:** The WhatsApp webhook endpoint (`/api/v1/webhooks/whatsapp`) accepted POST requests without verifying the `X-Hub-Signature-256` header, allowing attackers to spoof messages from Meta.
**Learning:** Webhook integrations often default to insecure configurations (trusting the payload) unless signature verification is explicitly implemented. In FastAPI, using a dependency for signature verification allows clean separation of security logic from business logic.
**Prevention:** Always implement signature verification for webhooks (Stripe, Slack, Meta, etc.) using `hmac.compare_digest` and ensure the secret is loaded from environment variables.
