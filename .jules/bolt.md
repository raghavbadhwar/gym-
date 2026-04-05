## 2024-04-05 - [SQLAlchemy Enum GroupBy Behavior]
**Learning:** When using `.group_by(Column)` on an Enum column in SQLAlchemy, the query result rows contain the actual Python Enum objects (e.g., `<MemberState.ACTIVE: 'active'>`) instead of raw string values if mapped via `sqlalchemy.Enum`.
**Action:** When building statistics dictionaries or mappings from a `group_by` result on an Enum, safely extract the string value using a fallback pattern like `state.value if hasattr(state, 'value') else state` to ensure compatibility and avoid `KeyError` issues when accessing the dictionary later.
