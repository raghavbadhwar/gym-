## 2024-04-28 - FastAPI Webhook Exception Swallowing
**Vulnerability:** A broad except Exception block in a FastAPI endpoint caught and suppressed HTTPException, causing the webhook to return 200 OK even on authentication failures.
**Learning:** FastAPI's HTTPException inherits from Exception. Catching it broadly and returning a success structure masks failures and creates fail-open flaws.
**Prevention:** Always explicitly catch and re-raise HTTPException before general except Exception blocks in FastAPI endpoints.
