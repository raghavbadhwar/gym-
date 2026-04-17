## 2026-04-17 - SQLAlchemy N+1 Queries in Aggregations
**Learning:** Performing multiple independent `.count()` queries filtering on different enum states in SQLAlchemy causes an N+1-like issue for simple aggregations, severely impacting database performance and overhead.
**Action:** Always replace multiple `.filter(Column == State).count()` operations with a single `.group_by(Column)` query mapped into a Python dictionary. Ensure to retain a separate un-grouped `.count()` query for totals to accurately include records with unmapped or NULL values.
