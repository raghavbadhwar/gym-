# Bolt Journal

## Performance Learnings

## 2025-02-17 - Optimize member stats aggregation
**Learning:** In SQLAlchemy, calculating statistics by aggregating individual `.count()` queries for different categories results in the N+1 query problem, where the application makes N separate database roundtrips.
**Action:** Use a single database `.group_by()` query with `func.count()` to aggregate the data on the database side and then process the result set in Python to extract the needed statistics. This drastically reduces database roundtrips and improves performance, especially over a remote database connection.
