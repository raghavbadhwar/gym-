## 2024-05-24 - Optimizing multiple COUNT queries with GROUP BY

**Learning:** When retrieving statistics for different states of an entity, performing a separate `COUNT` query for each state leads to multiple database roundtrips and degrades performance. Grouping the counts by state in a single query allows fetching all necessary statistics simultaneously. Note that when querying with SQLAlchemy `group_by` on an `Enum` column, the returned dictionary keys are Python Enum members (e.g., `MemberState.ACTIVE`), requiring lookup by the Enum object rather than its string value.

**Action:** Replace multiple `.count()` calls in a method with a single `.group_by()` query when retrieving distributions or counts by state/type. Always retrieve the resulting values using the Enum object keys.