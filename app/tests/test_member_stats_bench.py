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

def test_get_stats_performance(db_session, benchmark):
    # Setup - create many members
    for i in range(100):
        state = list(MemberState)[i % len(MemberState)]
        member = Member(
            phone=f"1234567{i}",
            name=f"User {i}",
            current_state=state
        )
        db_session.add(member)
    db_session.commit()

    service = MemberService(db_session)

    def run_stats():
        return service.get_stats()

    result = benchmark(run_stats)
    assert result['total'] == 100
