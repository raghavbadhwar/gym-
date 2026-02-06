## 2026-02-06 - Timing Attack Vulnerability in String Comparison
**Vulnerability:** Simple string comparison (`==` or `!=`) for API keys allows attackers to deduce the key length and content by measuring response times.
**Learning:** Python's standard string comparison returns as soon as a mismatch is found, creating a timing side-channel.
**Prevention:** Always use `secrets.compare_digest()` for comparing sensitive secrets (passwords, API keys, HMACs) as it runs in constant time.
