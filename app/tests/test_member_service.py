import pytest
from datetime import date, timedelta
from app.models.member import Member, MemberState
from app.services.member_service import MemberService

def test_get_stats(db_session):
    service = MemberService(db_session)

    # Create members with different states
    states = [
        MemberState.ACTIVE, MemberState.ACTIVE, MemberState.ACTIVE,
        MemberState.AT_RISK, MemberState.AT_RISK,
        MemberState.DORMANT,
        MemberState.NEW, MemberState.NEW, MemberState.NEW, MemberState.NEW,
        MemberState.CHURNED
    ]

    for i, state in enumerate(states):
        member = Member(
            phone=f"123456789{i}",
            name=f"Member {i}",
            current_state=state
        )
        db_session.add(member)
    db_session.commit()

    stats = service.get_stats()

    assert stats["total"] == 11
    assert stats["active"] == 3
    assert stats["at_risk"] == 2
    assert stats["dormant"] == 1
    assert stats["new"] == 4
    assert stats["churned"] == 1

    # Retention rate = (active / total) * 100 = (3 / 11) * 100 = 27.27... -> 27.3
    assert stats["retention_rate"] == 27.3

def test_get_stats_empty(db_session):
    service = MemberService(db_session)
    stats = service.get_stats()

    assert stats["total"] == 0
    assert stats["active"] == 0
    assert stats["retention_rate"] == 0
