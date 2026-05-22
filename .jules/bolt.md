## 2025-02-18 - N+1 in Aggregations
**Learning:** The application was making separate queries for each member state in `MemberService.get_stats`, leading to unnecessary database round-trips.
**Action:** Use `GROUP BY` and aggregation functions to fetch all stats in a single query. Check for similar patterns in other service methods.
