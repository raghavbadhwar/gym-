# Bolt's Journal

## 2024-05-22 - [Optimized Member Stats Query]
**Learning:** Replaced 6 separate `count()` queries with a single `GROUP BY` query in `MemberService.get_stats`. This reduces database roundtrips significantly on the dashboard overview.
**Action:** Look for other dashboard aggregation endpoints that might be making multiple queries instead of one.
