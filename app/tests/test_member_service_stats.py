import pytest
from app.services.member_service import MemberService
from app.models.member import Member, MemberState

def test_get_stats(db_session):
    service = MemberService(db_session)

    # Create test members with varying states
    members = [
        Member(phone="1", name="Active 1", current_state=MemberState.ACTIVE),
        Member(phone="2", name="Active 2", current_state=MemberState.ACTIVE),
        Member(phone="3", name="New 1", current_state=MemberState.NEW),
        Member(phone="4", name="At Risk 1", current_state=MemberState.AT_RISK),
        Member(phone="5", name="Dormant 1", current_state=MemberState.DORMANT),
        Member(phone="6", name="Churned 1", current_state=MemberState.CHURNED),
        Member(phone="7", name="Reactivated 1", current_state=MemberState.REACTIVATED),
    ]

    db_session.add_all(members)
    db_session.commit()

    # Get stats
    stats = service.get_stats()

    # Verify counts
    assert stats["total"] == 7
    assert stats["active"] == 2
    assert stats["new"] == 1
    assert stats["at_risk"] == 1
    assert stats["dormant"] == 1
    assert stats["churned"] == 1

    # Note: REACTIVATED is often counted as active or separately depending on business logic,
    # but the original implementation only counted explicit states.
    # Wait, the original implementation did NOT query for REACTIVATED.
    # Let's check the original implementation:
    # active = ... filter(Member.current_state == MemberState.ACTIVE)
    # So REACTIVATED was ignored in 'active' count.
    # Total count uses query(Member).count(), so it includes REACTIVATED.

    # Verify retention rate: active / total * 100
    # 2 / 7 * 100 = 28.57... -> 28.6
    assert stats["retention_rate"] == 28.6

def test_get_stats_empty(db_session):
    service = MemberService(db_session)
    stats = service.get_stats()

    assert stats["total"] == 0
    assert stats["active"] == 0
    assert stats["new"] == 0
    assert stats["at_risk"] == 0
    assert stats["dormant"] == 0
    assert stats["churned"] == 0
    assert stats["retention_rate"] == 0
