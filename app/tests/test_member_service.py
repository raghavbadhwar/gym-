import pytest
from app.services.member_service import MemberService
from app.models.member import Member, MemberState
from datetime import date
from sqlalchemy import event

def test_get_stats_query_count(db_session, engine):
    service = MemberService(db_session)

    # Create test data
    states = [
        MemberState.NEW,
        MemberState.ACTIVE, MemberState.ACTIVE,
        MemberState.AT_RISK,
        MemberState.DORMANT,
        MemberState.CHURNED,
    ]

    for i, state in enumerate(states):
        member = Member(
            phone=f"123456789{i}",
            name=f"Member {i}",
            current_state=state,
            membership_start=date.today(),
            membership_end=date.today()
        )
        db_session.add(member)
    db_session.commit()

    # Counter mechanism
    query_count = [0]
    def callback(conn, cursor, statement, parameters, context, executemany):
        query_count[0] += 1

    event.listen(engine, "before_cursor_execute", callback)

    try:
        stats = service.get_stats()
    finally:
        event.remove(engine, "before_cursor_execute", callback)

    # Verify correctness
    assert stats["total"] == 6
    assert stats["new"] == 1
    assert stats["active"] == 2
    assert stats["at_risk"] == 1
    assert stats["dormant"] == 1
    assert stats["churned"] == 1

    # Verify performance: Should be 1 query (grouped), definitely less than the original 6
    assert query_count[0] <= 2, f"Expected <= 2 queries, got {query_count[0]}"
