## 2026-06-22 - Refactor repeated COUNT queries to single GROUP BY query
**Learning:** Found multiple distinct database count queries in `get_stats` function in `member_service.py`. Each state was being queried with a separate `.count()` call causing unnecessary N+1 roundtrips.
**Action:** Replace multiple count queries with a single query using SQLAlchemy's `func.count()` and `group_by()` to execute the grouping operation efficiently at the database level.
