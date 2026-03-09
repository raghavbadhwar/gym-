## 2024-05-24 - Database Aggregations for Analytics Endpoints
**Learning:** Calculating aggregations (like sum of capacities or booked counts) in Python memory (`sum(c.capacity for c in classes)`) causes O(N) memory scaling and is a significant bottleneck for analytics endpoints tracking historical data.
**Action:** Always prefer database-level aggregations (`func.sum`, `func.count`, and `.group_by()`) to offload computation to the database and retrieve only the final aggregate values, massively reducing payload size and processing time.
