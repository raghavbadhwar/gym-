## 2025-02-12 - Insecure Default Configuration
**Vulnerability:** The application was initially configured with hardcoded secrets or insecure defaults in `app/config.py` (e.g., `admin_api_key`).
**Learning:** Defaulting to a "dev" secret in the codebase can lead to production deployments with known credentials. Security-critical settings must default to empty or secure-fail states.
**Prevention:** Use `BaseSettings` with no default value (making it required) or default to an empty string and explicitly check/fail in the application logic if the secret is missing.
