## 2026-02-02 - Unprotected Administrative Endpoints
**Vulnerability:** The `app/routers/members.py` endpoints (Create, Update, List members) were completely public, allowing anyone to access and modify member PII without authentication.
**Learning:** The application mixes public-facing chat endpoints (which require no auth or implicit phone-based auth) with administrative endpoints in the same API structure. This lack of separation led to administrative routes being exposed by default.
**Prevention:**
1. Segregate administrative routers from public routers.
2. Apply `dependencies=[Depends(get_admin_api_key)]` at the `APIRouter` level for all admin-focused modules.
3. Use a "secure by default" approach where a base `APIRouter` class or factory forces an auth dependency unless explicitly opted out.
