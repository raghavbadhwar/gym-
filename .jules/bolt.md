## Bolt's Performance Journal

This journal tracks critical learnings about codebase-specific performance patterns, bottlenecks, and surprises.

## 2024-05-24 - N+1 Query Prevention with Manual Joins
**Learning:** When using SQLAlchemy to optimize queries that already include a manual `.join()` (e.g., for filtering or ordering like `.join(Class).filter(...)`), using `.options(joinedload(relationship))` can create a redundant subquery or join. Instead, `.options(contains_eager(relationship))` is the optimal approach because it instructs SQLAlchemy to populate the related object from the columns already brought in by the existing `.join()`.
**Action:** Always check if a `.join()` already exists for the target relationship. If so, use `contains_eager` instead of `joinedload` to eliminate the N+1 query problem without introducing an extra redundant join into the generated SQL.
