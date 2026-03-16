## 2024-05-18 - Database-level Aggregation

**Learning:** When generating stats like class utilization, fetching all rows with `query(Class).all()` and aggregating capacities in Python is slow. This pattern scales poorly as records increase. Offloading `func.sum()` and `func.count()` with `.group_by()` to the database reduces memory and speeds up performance significantly (roughly 7x in tests).

**Action:** Whenever calculating metrics across multiple rows, use SQLAlchemy aggregations (`func.sum`, `func.count`, `.group_by`) rather than pulling the objects into Python memory to compute sums.
