
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.member import Member, MemberState
from app.services.member_service import MemberService

# Setup in-memory database for testing
engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

def test_get_stats(db):
    service = MemberService(db)

    # Create members with different states
    states = [
        MemberState.ACTIVE, MemberState.ACTIVE, MemberState.ACTIVE,
        MemberState.AT_RISK, MemberState.AT_RISK,
        MemberState.DORMANT,
        MemberState.CHURNED,
        MemberState.NEW, MemberState.NEW, MemberState.NEW, MemberState.NEW
    ]

    for i, state in enumerate(states):
        member = Member(
            phone=f"123456789{i}",
            name=f"Test Member {i}",
            current_state=state
        )
        db.add(member)
    db.commit()

    # Call get_stats
    stats = service.get_stats()

    # Verify counts
    assert stats["total"] == len(states)
    assert stats["active"] == 3
    assert stats["at_risk"] == 2
    assert stats["dormant"] == 1
    assert stats["churned"] == 1
    assert stats["new"] == 4

    # Verify retention rate
    # Active / Total * 100 = 3 / 11 * 100 = 27.27... -> 27.3
    assert stats["retention_rate"] == 27.3

def test_get_stats_empty_db(db):
    service = MemberService(db)
    stats = service.get_stats()

    assert stats["total"] == 0
    assert stats["active"] == 0
    assert stats["retention_rate"] == 0
