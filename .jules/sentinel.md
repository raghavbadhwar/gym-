## 2024-03-21 - Webhook Signature Validation & Fail Secure Strategy

**Vulnerability:**
The WhatsApp webhook endpoint (`/api/v1/webhooks/whatsapp`) lacked signature validation for incoming POST requests. This allowed any unauthenticated actor to spoof WhatsApp messages by simply knowing the endpoint URL. Furthermore, any exceptions generated during processing were masked by a catch-all block that returned a 200 OK, failing to securely abort processing when needed.

**Learning:**
1. **Missing Signature Validation:** Meta provides an `X-Hub-Signature-256` header (HMAC-SHA256) which must be verified against the app's secret.
2. **Fail Secure Override:** FastAPI dependencies and routers often rely on throwing `HTTPException` to interrupt requests and return appropriate 4xx/5xx status codes. Using a raw `except Exception as e:` block that returns an HTTP 200 JSON response incorrectly swallows intentional failures (like missing/invalid signature 401s, or unconfigured secret 500s). `HTTPException` must be caught and re-raised before general exception handlers.
3. **App Secret Misconfiguration:** If the `whatsapp_app_secret` is not set, the app cannot validate signatures. Rather than defaulting to allowing the request, a 'Fail Secure' strategy dictates that the app should reject the request with a 500 Internal Server Error.
4. **Timing Attacks:** Standard string comparisons (`==`) for hashes are vulnerable to timing attacks; always use `hmac.compare_digest` (or `secrets.compare_digest`).

**Prevention:**
- Always enforce webhook signature validation for third-party integrations using `hmac.compare_digest`.
- Ensure application secrets are required and validated at runtime, failing fast and securely if they are missing.
- When catching global exceptions to prevent framework retries (e.g., Meta retrying a 500), explicitly allow `HTTPException` to bubble up or handle it correctly so intentional security failures are not masked.