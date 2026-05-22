## 2026-02-24 - Missing Authentication on Administrative Endpoints

**Vulnerability:** The `members` and `classes` routers were completely public, exposing sensitive member data and allowing unauthorized modification of classes.
**Learning:** The application lacked a centralized authentication mechanism for administrative tasks. The focus was likely on the WhatsApp webhook which uses token verification, but the REST API was left unprotected.
**Prevention:** Implement a "secure by default" strategy where `APIRouter` instances for administrative domains (`members`, `classes`) are initialized with `dependencies=[Depends(auth_dependency)]` at the router level, ensuring all contained endpoints are protected automatically.
