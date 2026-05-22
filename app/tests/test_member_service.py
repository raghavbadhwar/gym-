
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.member import Member, MemberState
from app.services.member_service import MemberService

# Use in-memory DB for tests
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
    # Create members in different states
    states = [
        MemberState.NEW,
        MemberState.ACTIVE,
        MemberState.AT_RISK,
        MemberState.DORMANT,
        MemberState.CHURNED,
        MemberState.REACTIVATED
    ]

    # Add 100 members for each state
    for state in states:
        for i in range(100):
            member = Member(
                phone=f"+1555{state}{i}",
                name=f"Member {state} {i}",
                current_state=state
            )
            db_session.add(member)

    db_session.commit()

    service = MemberService(db_session)
    stats = service.get_stats()

    # Verify expected counts
    # Total should be sum of all states (6 * 100 = 600)
    assert stats["total"] == 600

    # Check specific counts
    assert stats["active"] == 100
    assert stats["at_risk"] == 100
    assert stats["dormant"] == 100
    assert stats["churned"] == 100
    assert stats["new"] == 100

    # Check retention rate calculation
    # Retention rate = (active / total) * 100 = (100 / 600) * 100 = 16.7
    assert stats["retention_rate"] == 16.7
