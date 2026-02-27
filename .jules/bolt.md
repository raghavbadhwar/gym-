# Bolt's Journal

## 2024-05-23 - [Initialization]
**Learning:** Performance monitoring requires a persistent record of insights.
**Action:** Created this journal to track critical performance learnings.

## 2024-05-23 - [SQLAlchemy Enum Group By]
**Learning:** When using SQLAlchemy's `group_by` on an Enum column, the returned dictionary keys are the Python Enum members (objects), not the string values stored in the database.
**Action:** Always access results using the Enum member (e.g., `MemberState.ACTIVE`) rather than the string literal "active" when processing `group_by` results.
