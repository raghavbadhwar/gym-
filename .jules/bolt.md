## 2026-03-29 - [Optimizing SQLAlchemy group_by]
**Learning:** When refactoring SQLAlchemy queries with `group_by` and extracting values to manually construct a total, it is much safer and accurate to use a dynamic sum (e.g., `sum(stats.values())`) instead of hardcoding specific states to avoid bugs if new states are added or if some members have a NULL state.
**Action:** Always sum the dynamically generated dictionary values when rebuilding a `total` variable from grouped queries instead of hardcoding expected keys.
