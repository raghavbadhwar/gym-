
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.services.member_service import MemberService
from app.models.member import Member, MemberState

@pytest.fixture
def db_session():
    # Use in-memory SQLite for fast testing
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

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

def test_get_stats_aggregated(db_session):
    # Add members with different states
    members = [
        Member(phone="1", name="Active1", current_state=MemberState.ACTIVE),
        Member(phone="2", name="Active2", current_state=MemberState.ACTIVE),
        Member(phone="3", name="New1", current_state=MemberState.NEW),
        Member(phone="4", name="AtRisk1", current_state=MemberState.AT_RISK),
        Member(phone="5", name="Dormant1", current_state=MemberState.DORMANT),
        Member(phone="6", name="Churned1", current_state=MemberState.CHURNED),
        Member(phone="7", name="Reactivated1", current_state=MemberState.REACTIVATED),
    ]
    db_session.add_all(members)
    db_session.commit()

    service = MemberService(db_session)
    stats = service.get_stats()

    # Total should include all members, including REACTIVATED
    assert stats["total"] == 7

    # Check individual counts
    assert stats["active"] == 2
    assert stats["new"] == 1
    assert stats["at_risk"] == 1
    assert stats["dormant"] == 1
    assert stats["churned"] == 1

    # Retention rate: Active / Total
    # 2 / 7 = 0.2857... -> 28.6%
    assert stats["retention_rate"] == 28.6

def test_get_stats_all_same_state(db_session):
    members = [
        Member(phone=str(i), name=f"Active{i}", current_state=MemberState.ACTIVE)
        for i in range(5)
    ]
    db_session.add_all(members)
    db_session.commit()

    service = MemberService(db_session)
    stats = service.get_stats()

    assert stats["total"] == 5
    assert stats["active"] == 5
    assert stats["new"] == 0
    assert stats["retention_rate"] == 100.0
