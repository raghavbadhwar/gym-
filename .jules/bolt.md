## 2025-03-09 - SQLAlchemy Query Optimization
**Learning:** In `MemberService.get_stats`, the original implementation queried the database for each member state individually using `.count()`, resulting in 6 separate database queries. This is a common performance bottleneck in backend applications.
**Action:** Replaced the 6 separate queries with a single query using SQLAlchemy's `func.count()` and `.group_by()` to aggregate the counts by state in one database call. Also mapped the results directly using the Enum instance.
