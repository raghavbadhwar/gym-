## 2024-03-14 - Optimize BookingService.get_utilization_stats
**Learning:** The `BookingService.get_utilization_stats` method was loading all `Class` objects into memory and performing aggregation manually. This causes a larger memory footprint and increases processing time.
**Action:** Always prefer pushing aggregations (like sum, count) to the database layer using SQLAlchemy's `func.sum`, `func.count`, and `.group_by()` rather than fetching all objects and doing the calculations in Python.
