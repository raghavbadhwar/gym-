## 2025-02-13 - FastAPI Webhook Fail-Open Vulnerability
**Vulnerability:** A generic `except Exception` handler was swallowing `HTTPException`s raised for invalid webhook signatures, causing the endpoint to return a 200 OK regardless, effectively bypassing authentication.
**Learning:** In FastAPI webhook patterns where broad exceptions are caught (to prevent retries from third parties like Meta), explicitly raised security exceptions (like 401 Unauthorized via `HTTPException`) get suppressed and converted into "success" responses if not explicitly re-raised.
**Prevention:** Always explicitly catch and re-raise `HTTPException` before any broad `except Exception` blocks in webhook or API endpoints to ensure security failures are accurately communicated back to the client/caller.
