## 2024-05-24 - Secure Admin Endpoints Configuration
**Vulnerability:** The application's administrative endpoints (`list_members`, `get_member_stats` in `app/routers/members.py`) lacked explicit authentication. An external attacker could call these endpoints and access PII or internal analytics, which should be restricted.
**Learning:** It's not enough to implement an authentication scheme; you must apply it. When configuring security dependencies like `get_admin_api_key`, a "Fail Secure" strategy should always be used. If an API key is unconfigured server-side, it is critical to raise an internal server error (500) rather than fail open and allow unauthorized access. Additionally, secret comparison must be done carefully to prevent timing attacks.
**Prevention:**
1. Always secure potentially sensitive endpoints proactively using `dependencies=[Depends(auth_dependency)]` or equivalent in routing setups.
2. For secret comparisons (e.g., API keys, tokens), always use `secrets.compare_digest` instead of simple string equality checks (`==`).
3. Always check if the required security configurations (environment variables) actually exist and actively reject all incoming requests if they are misconfigured.
