import pytest
from app.services.member_service import MemberService, MemberState
from app.models.member import Member
from datetime import date

def test_get_stats(db_session):
    # Setup: Create members with different states
    members_data = [
        {"name": "Alice", "phone": "1001", "current_state": MemberState.NEW},
        {"name": "Bob", "phone": "1002", "current_state": MemberState.ACTIVE},
        {"name": "Charlie", "phone": "1003", "current_state": MemberState.ACTIVE},
        {"name": "David", "phone": "1004", "current_state": MemberState.AT_RISK},
        {"name": "Eve", "phone": "1005", "current_state": MemberState.DORMANT},
        {"name": "Frank", "phone": "1006", "current_state": MemberState.CHURNED},
        {"name": "Grace", "phone": "1007", "current_state": MemberState.NEW},
    ]

    for data in members_data:
        member = Member(
            name=data["name"],
            phone=data["phone"],
            current_state=data["current_state"],
            membership_start=date.today(),
            membership_end=date.today()
        )
        db_session.add(member)
    db_session.commit()

    service = MemberService(db_session)
    stats = service.get_stats()

    assert stats["total"] == 7
    assert stats["new"] == 2
    assert stats["active"] == 2
    assert stats["at_risk"] == 1
    assert stats["dormant"] == 1
    assert stats["churned"] == 1

    # Retention rate: (active / total) * 100 = (2 / 7) * 100 = 28.6
    assert stats["retention_rate"] == 28.6
