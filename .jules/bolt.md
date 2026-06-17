## 2024-04-19 - Group By Enum Query Optimization Edge Case
**Learning:** When refactoring multiple scalar SQLAlchemy queries (like `.count()`) into a single query using `.group_by()` on an Enum column, using `sum()` on the grouped values to calculate a total can erroneously exclude rows with `NULL` or unmapped Enum values.
**Action:** Retain a separate explicit `.count()` query for the overall total instead of summing the grouped values, to ensure all members are accurately counted regardless of their enum state mapping.
