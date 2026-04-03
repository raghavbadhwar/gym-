The WhatsApp webhook endpoint (`app/routers/webhooks.py`) does not verify the incoming payload signature (`X-Hub-Signature-256`) against a secret from the App Dashboard.
This allows attackers to spoof requests pretending to be Meta.

According to my instructions: "The WhatsApp webhook endpoint (`/whatsapp` POST) in `app/routers/webhooks.py` enforces `X-Hub-Signature-256` validation; it requires `whatsapp_app_secret` to be set in the application configuration, actively employing a 'Fail Secure' strategy (raising an HTTP 500 error) if the secret is missing."

Steps:
1. Add `whatsapp_app_secret: str = ""` to `app/config.py` Settings class.
2. Update `app/routers/webhooks.py` `receive_message` function to:
   - Read the raw request body: `body = await request.body()`
   - Read the signature header: `signature = request.headers.get("X-Hub-Signature-256")`
   - If `settings.whatsapp_app_secret` is not set, raise 500.
   - If signature is missing, raise 401.
   - Compute expected signature with `hmac.new` and compare with `hmac.compare_digest`. Raise 401 if invalid.
3. Clean up `.jules/sentinel.md` adding this critical learning (if file doesn't exist, create it).
