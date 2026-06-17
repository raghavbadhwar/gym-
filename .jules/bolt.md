## 2024-05-24 - Pre-allocating fallback intents dictionary
**Learning:** In Python, creating a dictionary inside a method that is called frequently causes redundant object allocation. In `app/services/ai_service.py`, `_simple_intent_classification` was allocating a dictionary every time it ran.
**Action:** Extract static dictionaries to class-level or module-level constants to avoid redundant allocations and improve performance in high-frequency methods.
