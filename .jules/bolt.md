## 2024-05-30 - Enum Status Counts Optimization
**Learning:** Making repeated `.count()` queries to the database for every possible enum value (like `MemberState`) causes a severe N+1 query pattern that tanks performance as data scales.
**Action:** Consolidate these into a single `.query(Model.state_col, func.count(Model.id)).group_by(Model.state_col)` roundtrip, and map the results in memory. Note: SQLAlchemy returns the actual Enum object (e.g., `MemberState.ACTIVE`), not its string value, so dictionary access must use the Enum object itself.
