## 2025-06-03 - Overly Permissive CORS Configuration

**Vulnerability:** The FastAPI application used a hardcoded `allow_origins=["*"]` setting in `CORSMiddleware`, enabling any domain to send cross-origin requests to the API.
**Learning:** The hardcoded value was likely used for easier local development but carried over to production settings, completely bypassing browser CORS protections for API endpoints. Hardcoding an empty list (`allow_origins=[]`) disables CORS entirely and breaks the frontend.
**Prevention:** Always use environment configuration for security settings like CORS. Use a list comprehension (e.g., `[origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]`) alongside an environment variable (like `cors_origins`) that defaults to `*` for backward compatibility but allows strict lockdown in production.
