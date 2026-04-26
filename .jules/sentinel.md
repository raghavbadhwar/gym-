## 2025-04-26 - Webhook Signature Fail-Open Vulnerability
**Vulnerability:** The POST `/whatsapp` webhook endpoint handled all exceptions broadly (`except Exception as e`) and returned a 200 OK status to prevent Meta from retrying. However, this also caught `HTTPException`s thrown during signature validation, effectively resulting in a fail-open state where unauthorized or tampered requests would still return a 200 OK.
**Learning:** Broad exception handlers in webhooks can inadvertently swallow specific security-related HTTP errors, breaking authentication mechanisms and causing fail-open behavior.
**Prevention:** Always explicitly catch and re-raise `HTTPException` before falling back to general `Exception` blocks in FastAPI webhooks to ensure security constraints are correctly enforced.
