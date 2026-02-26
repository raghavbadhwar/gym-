## 2026-02-10 - Administrative API Protection
**Vulnerability:** Unauthenticated access to `/api/v1/members` exposed PII (Phone, Name, Weight) and administrative actions.
**Learning:** Default project templates often lack administrative authentication layers. Hardcoded default secrets in `config.py` (even for dev) are risky as they might be deployed inadvertently.
**Prevention:**
1. Use `Optional[str] = None` for sensitive keys in `Settings` to force explicit configuration.
2. Implement fail-closed logic: if key is missing, server should refuse to start or deny all requests (HTTP 500).
3. Use `dependency_overrides` to mock settings in tests, avoiding the need for default secrets.
