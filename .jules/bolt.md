## 2026-02-22 - Optimizing N+1 with contains_eager
**Learning:** When using SQLAlchemy's `query.join(Model)`, accessing the related model later (e.g. in a loop) triggers lazy loading (N+1 queries). Instead of adding `joinedload(Model)` which creates a redundant join, use `.options(contains_eager(Model))` to tell the ORM to populate the relationship using the *existing* join.
**Action:** Inspect queries that use manual joins. If the joined entity is accessed in the result, add `contains_eager` to the query options.
