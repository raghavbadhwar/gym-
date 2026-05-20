import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.member import Member, MemberState
from app.services.member_service import MemberService
from app.database import Base

@pytest.fixture
def db_session():
    # Use in-memory SQLite for testing
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

def test_get_stats_counts_correctly(db_session):
    service = MemberService(db_session)

    # Create members in various states
    members_data = [
        (MemberState.ACTIVE, 10),
        (MemberState.NEW, 5),
        (MemberState.AT_RISK, 3),
        (MemberState.DORMANT, 2),
        (MemberState.CHURNED, 4),
        (MemberState.REACTIVATED, 1) # Should count towards total but not specific buckets
    ]

    expected_total = 0
    for state, count in members_data:
        expected_total += count
        for i in range(count):
            member = Member(
                phone=f"+1555{state.value}{i}",
                name=f"Member {state.value} {i}",
                current_state=state
            )
            db_session.add(member)

    db_session.commit()

    stats = service.get_stats()

    assert stats["total"] == expected_total
    assert stats["active"] == 10
    assert stats["new"] == 5
    assert stats["at_risk"] == 3
    assert stats["dormant"] == 2
    assert stats["churned"] == 4

    # Calculate expected retention rate: (active / total) * 100
    expected_retention = round((10 / expected_total) * 100, 1)
    assert stats["retention_rate"] == expected_retention

def test_get_stats_empty_db(db_session):
    service = MemberService(db_session)
    stats = service.get_stats()

    assert stats["total"] == 0
    assert stats["active"] == 0
    assert stats["new"] == 0
    assert stats["at_risk"] == 0
    assert stats["dormant"] == 0
    assert stats["churned"] == 0
    assert stats["retention_rate"] == 0
