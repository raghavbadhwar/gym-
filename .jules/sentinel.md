## 2024-05-23 - Static Dashboard Security Challenge
**Vulnerability:** The backend API endpoints were unprotected, but the frontend (`dashboard/`) is a static site served separately or alongside, making secure authentication (like API keys) difficult without exposing secrets in client-side code.
**Learning:** Protecting APIs consumed by static frontends requires either a Backend-for-Frontend (BFF) pattern or user-based authentication (OAuth/JWT). Simply adding API keys to the backend breaks the frontend unless the key is hardcoded (insecure) or injected at runtime (complex for static files).
**Prevention:** For simple demos/prototypes, use Rate Limiting and Input Validation as the primary defense layers instead of weak authentication that provides a false sense of security.
