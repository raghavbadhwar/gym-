## 2024-05-20 - [Insecure Randomness in Token/Password Generation]
**Vulnerability:** Weak PRNG (`Math.random()`) used for generating OTP codes and default OAuth passwords in `BlockWalletDigi`.
**Learning:** `Math.random()` generates predictable values which breaks randomness constraints for security mechanisms, leading to possible predictability/brute-force of OTP codes and default passwords for users authenticated via OAuth.
**Prevention:** Use cryptographic PRNGs (`crypto.randomInt`, `crypto.randomBytes`) whenever generating sensitive security values.
