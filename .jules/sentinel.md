## 2024-05-30 - Prevent Timing Attacks in WhatsApp Webhook Verification
**Vulnerability:** The WhatsApp webhook verification endpoint (`/api/v1/webhooks/whatsapp`) was comparing the received `hub_verify_token` against the expected `settings.whatsapp_verify_token` using the standard `==` string equality operator.
**Learning:** Using `==` for comparing secrets like API keys or tokens exposes the application to timing attacks, where an attacker can determine the secret by measuring the time it takes for the comparison to fail.
**Prevention:** Always use `secrets.compare_digest` (or `hmac.compare_digest`) for comparing cryptographic secrets, API keys, or verification tokens to ensure constant-time comparison, mitigating timing attacks.
