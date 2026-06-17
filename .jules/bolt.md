## 2024-03-25 - SQLAlchemy Multiple COUNT() Optimization
**Learning:** Performing multiple individual `.count()` queries on the same table for different conditions (e.g., `filter(Member.current_state == X)`) results in multiple database roundtrips, causing significant performance overhead in Python/SQLAlchemy applications.
**Action:** Replace multiple scalar `.count()` calls with a single `GROUP BY` query (e.g., `.query(Model.column, func.count(Model.id)).group_by(Model.column)`) to calculate all aggregates in one database hit, extracting needed values from the resulting dictionary.
