## 2025-03-09 - Consolidate O(N) traversals
**Learning:** In backend data aggregation (like in `BookingService.get_utilization_stats`), calculating multiple aggregate properties across the same dataset using `sum()` multiple times incurs redundant iterations.
**Action:** Replace sequential passes with a single `for` loop to compute all aggregations at once, which improves raw execution time for large datasets without sacrificing readability.
