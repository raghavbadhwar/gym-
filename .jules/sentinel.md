## 2024-05-01 - Missing Constant-Time String Comparison
**Vulnerability:** Meta WhatsApp webhook GET verification (hub.verify_token) uses standard equality == instead of hmac.compare_digest.
**Learning:** Timing attacks can slowly leak token lengths and characters. When verifying incoming tokens/passwords, standard equality leaks timing information.
**Prevention:** Use hmac.compare_digest for all string comparisons involving secrets.
