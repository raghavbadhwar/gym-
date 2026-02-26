## 2024-05-22 - [Optimized Member Stats Query]
**Learning:** Replaced 6 separate database queries with a single `GROUP BY` query for dashboard statistics. This reduces database load and round-trip latency.
**Action:** When calculating stats for enum-based fields, always prefer `GROUP BY` over multiple `filter().count()` calls.
