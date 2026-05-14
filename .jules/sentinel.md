# Sentinel's Journal

## 2024-05-23 - Webhook Signature Verification
**Vulnerability:** Missing `X-Hub-Signature-256` verification on WhatsApp webhook endpoint allowed potential impersonation.
**Learning:** FastAPI/Starlette caches `request.body()`, allowing safe multiple reads for signature verification before JSON parsing.
**Prevention:** Use `app.services.security.validate_whatsapp_signature` for all webhook endpoints.
