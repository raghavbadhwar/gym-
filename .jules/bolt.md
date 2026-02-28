## 2024-05-24 - Group By queries for multiple counts

**Learning:** When retrieving count statistics for multiple possible states (e.g., active, dormant, new members), performing individual `.count()` queries for each state creates significant overhead by running N+1 queries (one for total + one per state). In a dataset that scales over time, this becomes a notable bottleneck. Additionally, `SQLAlchemy` returns dictionary keys as enum values rather than string representations when grouping by Enum columns.

**Action:** Replace multiple `.count()` calls with a single `GROUP BY` query (e.g., `db.query(Model.state_col, func.count(Model.id)).group_by(Model.state_col).all()`). Sum the resulting state counts to calculate the total without an additional query. Look up the resulting values using the Python Enum member directly, not its string value.
