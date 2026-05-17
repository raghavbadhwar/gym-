import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date, timedelta

from app.database import Base
from app.models.member import Member, MemberState
from app.services.member_service import MemberService

# Setup in-memory database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def db_session():
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

def test_get_stats(db_session):
    service = MemberService(db_session)

    # 1. Create members with different states
    # 2 Active
    m1 = service.create(phone="111", name="Active 1")
    service.update_state(m1, MemberState.ACTIVE)

    m2 = service.create(phone="222", name="Active 2")
    service.update_state(m2, MemberState.ACTIVE)

    # 1 New
    service.create(phone="333", name="New 1")

    # 1 At Risk
    m4 = service.create(phone="444", name="Risk 1")
    service.update_state(m4, MemberState.AT_RISK)

    # 0 Dormant

    # 1 Churned
    m5 = service.create(phone="555", name="Churned 1")
    service.update_state(m5, MemberState.CHURNED)

    # 2. Call get_stats
    stats = service.get_stats()

    # 3. Verify
    assert stats["total"] == 5
    assert stats["active"] == 2
    assert stats["new"] == 1
    assert stats["at_risk"] == 1
    assert stats["dormant"] == 0
    assert stats["churned"] == 1

    # Verify retention rate: (2 / 5) * 100 = 40.0
    assert stats["retention_rate"] == 40.0

def test_get_stats_empty(db_session):
    service = MemberService(db_session)
    stats = service.get_stats()

    assert stats["total"] == 0
    assert stats["active"] == 0
    assert stats["retention_rate"] == 0
