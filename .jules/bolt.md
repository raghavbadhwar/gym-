## 2024-04-15 - N+1 Query in Member Stats
**Learning:** Found multiple count() queries running sequentially for member statistics in `MemberService.get_stats`. This performs N separate database queries for N member states.
**Action:** Always use SQLAlchemy's `func.count()` combined with `.group_by()` to aggregate statistics in a single query when fetching counts by state/enum, reducing database roundtrips. Ensure total count remains a separate query to account for NULL states correctly.
