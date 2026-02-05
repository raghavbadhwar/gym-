import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.member import Base, Member, MemberState
from app.services.member_service import MemberService

# Setup in-memory database for testing
@pytest.fixture(scope="function")
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()

def test_get_stats(db_session):
    service = MemberService(db_session)

    # Create members
    # 2 Active
    m1 = service.create(phone="1", name="Active1")
    m1.current_state = MemberState.ACTIVE

    m2 = service.create(phone="2", name="Active2")
    m2.current_state = MemberState.ACTIVE

    # 1 New
    m3 = service.create(phone="3", name="New1")
    m3.current_state = MemberState.NEW

    # 1 At Risk
    m4 = service.create(phone="4", name="AtRisk1")
    m4.current_state = MemberState.AT_RISK

    # 1 Dormant
    m5 = service.create(phone="5", name="Dormant1")
    m5.current_state = MemberState.DORMANT

    # 1 Churned
    m6 = service.create(phone="6", name="Churned1")
    m6.current_state = MemberState.CHURNED

    # 1 Reactivated
    m7 = service.create(phone="7", name="Reactivated1")
    m7.current_state = MemberState.REACTIVATED

    db_session.commit()

    # Run get_stats
    stats = service.get_stats()

    # Verify counts
    # Reactivated is not in the specific keys, but should be in total
    assert stats["total"] == 7
    assert stats["active"] == 2
    assert stats["new"] == 1
    assert stats["at_risk"] == 1
    assert stats["dormant"] == 1
    assert stats["churned"] == 1

    # Verify retention rate
    # active / total = 2 / 7 = 0.2857... -> 28.6
    assert stats["retention_rate"] == 28.6
