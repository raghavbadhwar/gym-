## 2025-02-27 - Fastapi permissive CORS configuration

**Vulnerability:** Fastapi `CORSMiddleware` was overly permissive using hardcoded `allow_origins=["*"]`.
**Learning:** This exposes the application to Cross-Origin Resource Sharing attacks, allowing unauthorized websites to make requests as an authenticated user.
**Prevention:** Allow CORS origins to be loaded dynamically from environment variables, enabling administrators to set explicit lists of trusted origins in production, while defaulting to `*` for backward compatibility or local development. Ensure the environment variable is properly parsed to handle empty strings.
