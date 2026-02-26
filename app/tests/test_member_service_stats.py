import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date

from app.database import Base
from app.models.member import Member, MemberState
from app.services.member_service import MemberService

# Setup in-memory database
@pytest.fixture(scope="function")
def db_session():
    # Use StaticPool to ensure data persists for the session duration
    from sqlalchemy.pool import StaticPool
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_get_stats(db_session):
    service = MemberService(db_session)

    # Create members with different states
    members_data = [
        {"phone": "1", "name": "Active1", "current_state": MemberState.ACTIVE},
        {"phone": "2", "name": "Active2", "current_state": MemberState.ACTIVE},
        {"phone": "3", "name": "New1", "current_state": MemberState.NEW},
        {"phone": "4", "name": "AtRisk1", "current_state": MemberState.AT_RISK},
        {"phone": "5", "name": "Dormant1", "current_state": MemberState.DORMANT},
        {"phone": "6", "name": "Churned1", "current_state": MemberState.CHURNED},
        {"phone": "7", "name": "Active3", "current_state": MemberState.ACTIVE},
    ]

    for data in members_data:
        member = Member(
            phone=data["phone"],
            name=data["name"],
            current_state=data["current_state"],
            membership_start=date.today(),
            membership_end=date.today()
        )
        db_session.add(member)

    db_session.commit()

    stats = service.get_stats()

    assert stats["total"] == 7
    assert stats["active"] == 3
    assert stats["new"] == 1
    assert stats["at_risk"] == 1
    assert stats["dormant"] == 1
    assert stats["churned"] == 1

    # Verify retention rate: (3 active / 7 total) * 100 = 42.857... -> 42.9
    expected_retention = round((3 / 7) * 100, 1)
    assert stats["retention_rate"] == expected_retention

def test_get_stats_empty(db_session):
    service = MemberService(db_session)
    stats = service.get_stats()

    assert stats["total"] == 0
    assert stats["active"] == 0
    assert stats["retention_rate"] == 0
