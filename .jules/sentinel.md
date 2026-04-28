## 2024-05-24 - Webhook Signature Verification Security Vulnerability
**Vulnerability:** Fast API webhook was verifying WhatsApp GET payload payload but skipping signature check on POST messages, causing fail-open state for incoming messages
**Learning:** Even if webhook challenges are verified correctly via GET params, webhook POST payloads need constant-time string comparison for Meta signatures to prevent timing attacks.
**Prevention:** Verify incoming POST payloads by comparing the `X-Hub-Signature-256` header against the expected hash of the raw payload using `hmac.compare_digest`
