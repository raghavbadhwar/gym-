## 2024-05-22 - Missing Webhook Signature Verification
**Vulnerability:** The WhatsApp webhook endpoint (`/api/v1/webhooks/whatsapp`) accepted POST requests without verifying the `X-Hub-Signature-256` header, allowing anyone to impersonate Meta and inject fake messages.
**Learning:** Frameworks often make it easy to expose endpoints but don't enforce signature verification by default. The absence of a "security" module or specific auth dependency for webhooks is a red flag.
**Prevention:** Always implement HMAC signature verification for any public webhook endpoint. Use a dedicated security dependency to enforce this check before the request body is processed.
