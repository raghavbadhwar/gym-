from app.services.member_service import MemberService
from app.models.member import Member, MemberState
from datetime import date

def test_get_stats(db_session):
    service = MemberService(db_session)

    # Create members with different states
    members_data = [
        (MemberState.ACTIVE, 3),
        (MemberState.NEW, 2),
        (MemberState.AT_RISK, 1),
        (MemberState.DORMANT, 1),
        (MemberState.CHURNED, 2),
        (MemberState.REACTIVATED, 1) # Should contribute to total
    ]

    count_map = {}

    for state, count in members_data:
        count_map[state] = count
        for i in range(count):
            member = Member(
                phone=f"{state}{i}",
                name=f"Test {state} {i}",
                current_state=state,
                membership_start=date.today(),
                membership_end=date.today()
            )
            db_session.add(member)

    db_session.commit()

    stats = service.get_stats()

    total_expected = sum(count for _, count in members_data)

    assert stats["total"] == total_expected
    assert stats["active"] == count_map[MemberState.ACTIVE]
    assert stats["new"] == count_map[MemberState.NEW]
    assert stats["at_risk"] == count_map[MemberState.AT_RISK]
    assert stats["dormant"] == count_map[MemberState.DORMANT]
    assert stats["churned"] == count_map[MemberState.CHURNED]

    # Check retention rate
    active_count = count_map[MemberState.ACTIVE]
    expected_retention = round((active_count / total_expected) * 100, 1)
    assert stats["retention_rate"] == expected_retention
