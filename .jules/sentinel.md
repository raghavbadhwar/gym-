## 2026-01-29 - Missing Auth on Admin Routers
**Vulnerability:** `app/routers/members.py` and `app/routers/classes.py` were exposing sensitive member data and operations without any authentication.
**Learning:** The project seems to separate "Chat" (public) from "Admin" (private) logic but lacked a mechanism to enforce this separation at the API level. The chat router is public by design, which makes it easy to forget that other routers need protection.
**Prevention:** Ensure all new routers dealing with PII or admin operations include the `get_admin_api_key` dependency by default.
