## 2026-01-27 - [SQLAlchemy Count Optimization]
**Learning:** Multiple `count()` queries on the same table with different filters are significantly slower than a single `GROUP BY` query, even in SQLite.
**Action:** Use `db.query(Model.field, func.count(Model.id)).group_by(Model.field)` to aggregate stats in a single round-trip.
