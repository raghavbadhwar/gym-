## 2025-01-31 - Optimize Member Statistics with GROUP BY
**Learning:** `MemberService.get_stats` was making 6 separate database calls to count members in different states. Replacing this with a single `GROUP BY` query reduced execution time by ~6.5x (from ~7.8ms to ~1.2ms for 1000 records).
**Action:** When aggregating counts by a categorical column (like `current_state`), always prefer `db.query(Column, func.count(ID)).group_by(Column)` over multiple `.filter().count()` queries.
