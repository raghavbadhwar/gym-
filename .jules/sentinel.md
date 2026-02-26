# Sentinel's Journal

## 2024-05-23 - [Missing Webhook Authentication]
**Vulnerability:** The WhatsApp webhook endpoint (`/api/v1/webhooks/whatsapp`) was accepting all POST requests without verifying the `X-Hub-Signature-256` header.
**Learning:** Webhook endpoints often default to "public" because they need to be reachable by external services (Meta), leading to a common oversight where authentication is forgotten. Developers might assume the URL itself is secret or rely on obscurity.
**Prevention:** Always enforce signature verification for webhooks. Use a middleware or dependency that checks the signature against a shared secret before processing the body.
