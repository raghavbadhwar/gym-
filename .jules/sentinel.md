# Sentinel's Journal - Critical Security Learnings

## 2024-05-23 - [Missing Authentication on Management API]
**Vulnerability:** The `members` and `classes` API routers were completely unprotected, allowing full public access to sensitive member data and booking management.
**Learning:** These endpoints were likely intended for an internal dashboard but were exposed publicly without auth. The static dashboard demo uses different endpoints (`/chat`, `/webhooks`), masking the exposure of the management API.
**Prevention:** Always apply `dependencies=[Depends(auth)]` at the `APIRouter` level for administrative sections, and ensure a "fail-closed" mechanism (like `get_admin_api_key` raising 500 if no key is configured) prevents accidental exposure in default configurations.
