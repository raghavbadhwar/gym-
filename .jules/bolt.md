## 2024-03-20 - N+1 Query in Member Stats
**Learning:** Found an N+1 query issue in `MemberService.get_stats()` where multiple count queries were being executed sequentially for different member states. This causes unnecessary database roundtrips and degrades performance as the member base grows.
**Action:** Replaced multiple `.count()` queries with a single `.group_by()` query to aggregate counts by state in a single database trip, extracting counts with `.get(state, 0)` for safety.
