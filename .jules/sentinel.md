## 2026-02-18 - Missing Webhook Signature Verification
**Vulnerability:** The WhatsApp webhook endpoint (`/api/v1/webhooks/whatsapp`) was accepting POST requests without validating the `X-Hub-Signature-256` header, allowing attackers to forge messages.
**Learning:** Default framework implementations for webhooks often lack security checks. Missing `HMAC` verification is a common oversight in "getting started" code.
**Prevention:** Implement mandatory `X-Hub-Signature-256` verification for all Meta/WhatsApp webhooks. Ensure secret keys are required configuration in production.
