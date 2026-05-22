## 2025-02-12 - Critical Webhook Authentication Gap

**Vulnerability:** The WhatsApp webhook endpoint was accepting POST requests without validating the `X-Hub-Signature-256` header.
**Learning:** Even when using "verify tokens" for the initial handshake (GET), the actual message delivery (POST) requires a separate signature verification mechanism (HMAC-SHA256) which is often overlooked because it requires raw body access.
**Prevention:** Always implement signature verification for webhooks immediately. Use a dependency that reads the raw body safely (without consuming the stream if possible, or using frameworks that cache it like FastAPI) to validate the signature before processing any logic.
