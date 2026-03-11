## 2025-02-28 - Timing Attack in Webhook Verification
**Vulnerability:** The WhatsApp webhook verification route used a simple string equality check (`==`) to compare the incoming verification token with the configured secret token.
**Learning:** Standard string equality operators fail quickly as soon as a character doesn't match. In an attacker's hands, this allows them to perform a timing attack by observing the response time to guess the secret character by character.
**Prevention:** Always use `secrets.compare_digest()` (or `hmac.compare_digest()`) to perform constant-time string comparisons when checking secrets or verifying signatures.
