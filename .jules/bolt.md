## 2024-03-24 - SQLAlchemy Enum Group By Returns Objects

**Learning:** When using SQLAlchemy `group_by` on a column mapped to a Python Enum (e.g. `Member.current_state`), the query results contain the actual Enum objects (like `MemberState.ACTIVE`) rather than their underlying string values (like `"active"`). Furthermore, `func.count(Member.id)` correctly counts the rows, but you must sum these counts in Python to get the total instead of issuing another `.count()` query.

**Action:** When migrating multiple `.count()` queries into a single `.group_by()` query for performance, always use the Enum objects directly as dictionary keys (e.g. `counts_dict.get(MemberState.ACTIVE, 0)`) rather than strings, and manually sum the grouped results to calculate the overall total without additional DB roundtrips.
