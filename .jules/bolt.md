## 2026-02-25 - [Optimization] Member Stats N+1 Query
**Learning:** `get_stats` was executing 6 separate `count()` queries (one for each state). Using `GROUP BY` reduced this to 1 query.
**Action:** When aggregating counts by category, always prefer `GROUP BY` over multiple filtered counts.
