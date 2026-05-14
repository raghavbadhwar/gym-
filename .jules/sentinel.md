## 2026-02-07 - Missing Webhook Signature Verification

**Vulnerability:** The WhatsApp webhook endpoint (`/api/v1/webhooks/whatsapp`) was accepting requests without verifying the `X-Hub-Signature-256` header, allowing anyone to spoof messages.
**Learning:** External integration endpoints (like webhooks) must always verify origin authenticity. Relying on "hidden" URLs is insufficient. FastAPI dependencies (`Depends`) are an effective way to enforce this check without polluting business logic.
**Prevention:** Always implement signature verification middleware or dependencies for all public-facing webhook endpoints. Ensure the verification logic handles raw request body correctly (as `await request.body()` caches the body for subsequent reads).
