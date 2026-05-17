
import pytest
from app.models.member import Member, MemberState
from app.services.member_service import MemberService

def test_get_stats_correctness(db_session):
    """
    Verify that get_stats correctly counts members in different states
    and calculates retention rate.
    """
    # Seed data
    states = [
        MemberState.ACTIVE, MemberState.ACTIVE,
        MemberState.AT_RISK,
        MemberState.NEW, MemberState.NEW, MemberState.NEW,
        MemberState.DORMANT,
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

    service = MemberService(db_session)
    stats = service.get_stats()

    # Verify counts
    assert stats["total"] == 8
    assert stats["active"] == 2
    assert stats["at_risk"] == 1
    assert stats["new"] == 3
    assert stats["dormant"] == 1
    assert stats["churned"] == 1

    # Verify retention rate calculation: (active / total) * 100
    # (2 / 8) * 100 = 25.0
    assert stats["retention_rate"] == 25.0

def test_get_stats_empty(db_session):
    """Verify get_stats works correctly with empty database."""
    service = MemberService(db_session)
    stats = service.get_stats()

    assert stats["total"] == 0
    assert stats["active"] == 0
    assert stats["retention_rate"] == 0
