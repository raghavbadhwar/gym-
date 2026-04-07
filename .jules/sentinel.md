## 2024-05-18 - Missing Webhook Authentication
**Vulnerability:** The WhatsApp webhook endpoint (`POST /whatsapp`) did not authenticate incoming requests, allowing any external party to forge requests and inject malicious payloads or spoof messages.
**Learning:** In FastAPI, it's essential to catch and re-raise `HTTPException` explicitly in endpoints that have a broad `except Exception:` block; otherwise, deliberate error responses like `401 Unauthorized` get swallowed and return as a `200 OK`.
**Prevention:** Implement `X-Hub-Signature-256` HMAC validation for all webhooks. Ensure `HTTPException` is explicitly handled before generic exceptions. Use a fail-secure approach (returning 401) while gracefully bypassing if the secret is unconfigured to prevent breaking existing deployments.
