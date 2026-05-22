## 2025-02-15 - Composite Index for Conversation History
**Learning:** SQLite's query planner is smart enough to use a composite index `(member_id, created_at)` to satisfy both the filter on `member_id` and the `ORDER BY created_at` clause, avoiding an explicit `USE TEMP B-TREE FOR ORDER BY` step.
**Action:** Always prefer composite indexes for queries involving filtering + sorting on related columns.
