## 2024-04-22 - Optimize Multiple State Counts with Group By Query
**Learning:** When retrieving member statistics by state, executing separate `.count()` queries for each state is inefficient, resulting in multiple database round trips.
**Action:** Replace multiple separate state queries with a single `.group_by(Member.current_state)` query, allowing the database to aggregate counts efficiently in one operation. Keep a separate query for the total count to handle members with NULL or unmapped states.
