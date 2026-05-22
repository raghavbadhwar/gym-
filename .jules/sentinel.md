## 2026-02-14 - Unprotected Administrative API Endpoints
**Vulnerability:** The member management API (`/api/v1/members`, `/api/v1/classes`, `/api/v1/chat`) was completely unprotected, allowing unauthorized access to create, read, update, and delete member data (PII) and generate diet/workout plans.
**Learning:** Default router configurations in FastAPI do not enforce authentication unless explicitly added. The "demo" nature of the application led to security being overlooked on critical endpoints.
**Prevention:** Always apply authentication dependencies (`Depends(get_current_user)` or similar) at the `APIRouter` level for any endpoint handling sensitive data, even in development or demo applications.
