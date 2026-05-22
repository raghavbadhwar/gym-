import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.member import Member, MemberState
from app.services.member_service import MemberService
import uuid

# Use in-memory SQLite for tests
@pytest.fixture(scope="function")
def db():
    # Setup
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    # Teardown
    session.close()

def test_get_stats(db):
    service = MemberService(db)

    # Create members with different states
    states = [
        MemberState.NEW,
        MemberState.ACTIVE,
        MemberState.AT_RISK,
        MemberState.DORMANT,
        MemberState.CHURNED,
        MemberState.REACTIVATED
    ]

    # Create 10 of each
    for state in states:
        for i in range(10):
            member = Member(
                id=str(uuid.uuid4()),
                phone=f"123{state.value}{i}",
                name=f"User {state.value} {i}",
                current_state=state
            )
            db.add(member)
    db.commit()

    # Get stats
    stats = service.get_stats()

    # Verify counts
    # Reactivated is not returned explicitly but counted in total
    # 6 states * 10 members = 60 total
    expected_total = 60
    expected_active = 10

    assert stats["total"] == expected_total
    assert stats["active"] == expected_active
    assert stats["at_risk"] == 10
    assert stats["dormant"] == 10
    assert stats["churned"] == 10
    assert stats["new"] == 10

    # Calculate retention rate manually: (active / total) * 100
    # 10 / 60 = 0.1666... -> 16.7
    expected_retention = round((10 / 60) * 100, 1)
    assert stats["retention_rate"] == expected_retention
