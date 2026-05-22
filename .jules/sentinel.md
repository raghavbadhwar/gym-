## 2026-02-22 - Missing Configuration Security Gap
**Vulnerability:** The project was missing the `WHATSAPP_APP_SECRET` configuration variable in `Settings`, despite documentation/memory suggesting its presence.
**Learning:** Configuration drift is a common security gap. Always verify that security-critical configuration variables are actually present in the `Settings` class and environment files, not just documented.
**Prevention:** Implement checks in the startup logic or CI/CD to verify presence of critical security variables.
