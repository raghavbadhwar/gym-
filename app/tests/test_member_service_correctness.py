import pytest
from app.services.member_service import MemberService
from app.models.member import Member, MemberState
from unittest.mock import MagicMock
from app.database import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_get_stats_correctness(db_session):
    # Setup - create members in different states
    states = [
        MemberState.ACTIVE, MemberState.ACTIVE,  # 2 active
        MemberState.NEW,                         # 1 new
        MemberState.DORMANT, MemberState.DORMANT,# 2 dormant
        MemberState.CHURNED                      # 1 churned
        # 0 at_risk
    ]

    for i, state in enumerate(states):
        member = Member(
            phone=f"1234567{i}",
            name=f"User {i}",
            current_state=state
        )
        db_session.add(member)
    db_session.commit()

    service = MemberService(db_session)
    stats = service.get_stats()

    assert stats["total"] == 6
    assert stats["active"] == 2
    assert stats["new"] == 1
    assert stats["dormant"] == 2
    assert stats["churned"] == 1
    assert stats["at_risk"] == 0
    assert stats["retention_rate"] == 33.3  # (2/6)*100 = 33.333... -> 33.3
