## 2024-05-21 - Composite Indexes for History Tables
**Learning:** For tables where queries are almost exclusively filtered by a tenant/user ID and then sorted by time (like chat history), a composite index `(tenant_id, created_at)` is vastly superior to individual indexes. It allows the database to jump to the tenant's range and scan in order, avoiding a separate sort step.
**Action:** Always check for this pattern in new tables involving event logs or history.
