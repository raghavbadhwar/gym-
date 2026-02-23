# Sentinel Journal - Critical Security Learnings

## 2026-02-23 - Unprotected Administrative Endpoints
**Vulnerability:** The `/api/v1/members` and `/api/v1/classes` endpoints were completely public, exposing all member PII (names, phone numbers, weight, goals) and allowing unauthorized modifications.
**Learning:** Default router configuration in FastAPI (`include_router`) does not apply authentication by default. Developers must explicitly add `dependencies` to `APIRouter` or `include_router`.
**Prevention:** Always verify authentication requirements for new routers. Use `dependencies=[Depends(get_current_user)]` (or similar) at the router level for administrative sections.
