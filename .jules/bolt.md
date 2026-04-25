## 2025-04-25 - Group By Enum Lookup Issue
**Learning:** When refactoring SQLAlchemy queries to use `.group_by()` on Enum columns, let SQLAlchemy handle Enum mapping natively by mapping the raw state object directly as the dictionary key (e.g., `{state: count}`) and looking up using the Enum instance (e.g., `.get(MemberState.ACTIVE, 0)`). Avoid manually parsing `.name`, `.value`, or `str()` which can cause KeyErrors or fragile key matching during dictionary lookup.
**Action:** Use native Enum instances as dictionary keys when aggregating counts in SQLAlchemy queries.
