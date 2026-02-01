## 2024-05-22 - [Missing Authentication on PII Endpoints]
**Vulnerability:** The `app/routers/members.py` endpoints were completely unprotected, allowing unauthorized access to member PII (phone, name, stats) and administrative actions.
**Learning:** Default router configurations in FastAPI do not imply security. Separation of concerns (frontend vs backend) often leads to forgetting backend auth when the frontend (dashboard) seems to "just work".
**Prevention:**
1. Always audit new routers for `dependencies=[Depends(auth)]`.
2. Use a "secure by default" approach where the base `APIRouter` or middleware enforces auth unless explicitly exempted.
3. Test endpoints with `TestClient` without auth to ensure 401/403 is returned.
