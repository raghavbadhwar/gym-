## 2026-06-07 - Secure CORS Configuration
**Vulnerability:** Overly permissive CORS configuration (`allow_origins=["*"]`) hardcoded in `app/main.py`.
**Learning:** Hardcoded wildcards in CORS middleware prevent secure environment-specific policies, exposing production APIs to cross-origin attacks from any domain.
**Prevention:** Always extract security policies to configuration variables (e.g., `cors_origins`) and parse them dynamically via list comprehension to safely handle default/empty strings.
