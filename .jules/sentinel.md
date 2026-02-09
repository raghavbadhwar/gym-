## 2026-02-09 - Unauthenticated Administrative Endpoints
**Vulnerability:** The `/api/v1/members/` endpoints were accessible without any authentication, allowing unrestricted access to member data and CRUD operations.
**Learning:** The router was defined without any `dependencies` argument, and no authentication check was implemented in the individual route handlers. This gap existed because the focus was likely on the webhook/AI functionality, leaving the administrative API exposed.
**Prevention:** Enforce authentication dependencies at the router level (using `APIRouter(dependencies=[Depends(auth)])`) for all administrative or sensitive resource routers.
