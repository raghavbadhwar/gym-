import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.member import Member, MemberState
from app.services.member_service import MemberService
from app.database import Base

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_get_stats(db_session):
    service = MemberService(db_session)

    # Add members with different states
    # 2 Active
    m1 = service.create(phone="1", name="Active 1")
    service.update_state(m1, MemberState.ACTIVE)
    m2 = service.create(phone="2", name="Active 2")
    service.update_state(m2, MemberState.ACTIVE)

    # 1 New (default is NEW)
    service.create(phone="3", name="New 1")

    # 3 Churned
    m4 = service.create(phone="4", name="Churned 1")
    service.update_state(m4, MemberState.CHURNED)
    m5 = service.create(phone="5", name="Churned 2")
    service.update_state(m5, MemberState.CHURNED)
    m6 = service.create(phone="6", name="Churned 3")
    service.update_state(m6, MemberState.CHURNED)

    # 0 Dormant, 0 At Risk

    stats = service.get_stats()

    assert stats["total"] == 6
    assert stats["active"] == 2
    assert stats["new"] == 1
    assert stats["churned"] == 3
    assert stats["dormant"] == 0
    assert stats["at_risk"] == 0

    # Check retention rate (2 active / 6 total = 33.3%)
    assert stats["retention_rate"] == 33.3
