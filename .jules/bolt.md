## 2024-05-24 - Composite Index for Filter and Sort Queries
**Learning:** In SQLAlchemy, creating separate `index=True` on `member_id` and `created_at` doesn't optimize queries that both filter on `member_id` and order by `created_at` (e.g., fetching conversation history). A composite index is needed to fully optimize this pattern.
**Action:** Replace single-column indexes with a composite index using `__table_args__ = (Index('ix_name', 'col1', 'col2'),)` when optimizing queries that filter by one column and sort by another.
