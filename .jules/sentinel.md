## 2024-05-22 - Unprotected Administrative Endpoints
**Vulnerability:** Critical administrative endpoints (Member management, Class creation) in `app/routers/members.py` and `app/routers/classes.py` were completely exposed without any authentication.
**Learning:** The application architecture lacked a centralized authentication mechanism for API endpoints, relying implicitly on obscurity or future implementation. The `dashboard` demo UI communicates via public `chat` endpoints, masking the exposure of the admin API.
**Prevention:** Implemented `get_admin_api_key` dependency with a fail-secure default (denies access if key is not configured). Applied this dependency globally to `members_router` and selectively to write-operations in `classes_router`.
