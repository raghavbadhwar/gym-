## 2024-05-22 - MemberService State Management
**Learning:** `MemberService.create` hardcodes `current_state=MemberState.NEW`, ignoring `kwargs`. To test other states, you must create the member first and then call `update_state`.
**Action:** When testing state-dependent logic in `MemberService`, always use `create` followed by `update_state` to set up test data.

## 2024-05-22 - N+1 in Statistics
**Learning:** Dashboard statistics were fetching counts with 6 separate queries.
**Action:** Use `func.count` and `func.sum(case(...))` to aggregate multiple counts in a single query.
