import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.member import Member, MemberState
from app.database import Base
from app.services.member_service import MemberService
import uuid

@pytest.fixture
def db_session():
    # Use in-memory SQLite for testing
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_get_stats_counts(db_session):
    service = MemberService(db_session)

    # Clean state
    assert service.get_stats()["total"] == 0

    # Create members in different states
    states = [
        MemberState.ACTIVE, MemberState.ACTIVE, MemberState.ACTIVE,
        MemberState.AT_RISK, MemberState.AT_RISK,
        MemberState.DORMANT,
        MemberState.CHURNED,
        MemberState.NEW, MemberState.NEW,
    ]

    for i, state in enumerate(states):
        member = Member(
            name=f"Member {i}",
            phone=f"+123456789{i}",
            current_state=state,
            id=uuid.uuid4()
        )
        db_session.add(member)

    db_session.commit()

    stats = service.get_stats()

    assert stats["total"] == 9
    assert stats["active"] == 3
    assert stats["at_risk"] == 2
    assert stats["dormant"] == 1
    assert stats["churned"] == 1
    assert stats["new"] == 2

    # Retention rate: active / total * 100
    # 3 / 9 * 100 = 33.333... -> 33.3
    assert stats["retention_rate"] == 33.3
