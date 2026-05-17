## 2024-05-23 - SQLAlchemy Group By on Enum
**Learning:** When using SQLAlchemy's `group_by` on a column defined as an `Enum`, the resulting dictionary keys are the Python Enum members themselves, not their string values. This requires looking up values using the Enum object (e.g., `MemberState.ACTIVE`) rather than string literals.
**Action:** When optimizing aggregation queries involving Enums, always verify the return type of the grouping key and use the Enum class for dictionary lookups to ensure correctness.

## 2024-05-23 - Single Query Aggregation
**Learning:** Replacing multiple `count()` queries with a single `GROUP BY` query significantly reduces database round-trips.
**Action:** Always look for opportunities to aggregate data in a single query when calculating statistics or summaries.
