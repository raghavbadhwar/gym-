import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.member import Member, MemberState
from app.services.member_service import MemberService
from app.database import Base

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def db_session():
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_get_stats(db_session):
    service = MemberService(db_session)

    # Create members and update their states
    states = [
        MemberState.NEW,
        MemberState.ACTIVE, MemberState.ACTIVE,
        MemberState.AT_RISK,
        MemberState.DORMANT,
        MemberState.CHURNED,
        MemberState.REACTIVATED
    ]

    for i, state in enumerate(states):
        member = service.create(
            phone=f"123456789{i}",
            name=f"Test Member {i}"
        )
        if state != MemberState.NEW:
            service.update_state(member, state)

    stats = service.get_stats()

    assert stats["total"] == 7
    assert stats["active"] == 2
    assert stats["new"] == 1
    assert stats["at_risk"] == 1
    assert stats["dormant"] == 1
    assert stats["churned"] == 1

    # retention_rate = (active / total) * 100 = (2 / 7) * 100 = 28.57... -> 28.6
    assert stats["retention_rate"] == 28.6

def test_get_stats_empty(db_session):
    service = MemberService(db_session)
    stats = service.get_stats()

    assert stats["total"] == 0
    assert stats["active"] == 0
    assert stats["retention_rate"] == 0
