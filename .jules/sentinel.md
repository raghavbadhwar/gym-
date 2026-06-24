## 2025-06-24 - [CRITICAL] Prevent DoS in hmac.compare_digest
**Vulnerability:** The application was passing strings directly to `hmac.compare_digest()` for webhook verification token validation.
**Learning:** `hmac.compare_digest()` in Python does not support comparing strings containing non-ASCII characters and will throw a `TypeError`. An attacker could exploit this by sending a token with a non-ASCII character (e.g., `ñ`), causing an unhandled exception that results in an HTTP 500 error, acting as a Denial of Service (DoS) vulnerability.
**Prevention:** Always explicitly encode strings to bytes (e.g., `.encode('utf-8')`) before passing them to `hmac.compare_digest()`.
