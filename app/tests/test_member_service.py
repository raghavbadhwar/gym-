
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import date, timedelta

from app.database import Base
from app.models.member import Member, MemberState, PrimaryGoal
from app.services.member_service import MemberService

# Setup in-memory DB for testing
@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

def test_get_stats(db_session):
    service = MemberService(db_session)

    # Helper to create member with specific state
    def create_member(phone, name, state):
        m = service.create(phone=phone, name=name)
        m.current_state = state
        db_session.commit()
        return m

    # Create members with different states
    # 2 Active
    create_member(phone="1", name="Active 1", state=MemberState.ACTIVE)
    create_member(phone="2", name="Active 2", state=MemberState.ACTIVE)

    # 1 New
    create_member(phone="3", name="New 1", state=MemberState.NEW)

    # 3 At Risk
    create_member(phone="4", name="Risk 1", state=MemberState.AT_RISK)
    create_member(phone="5", name="Risk 2", state=MemberState.AT_RISK)
    create_member(phone="6", name="Risk 3", state=MemberState.AT_RISK)

    # 0 Dormant (to test missing state)

    # 1 Churned
    create_member(phone="7", name="Churned 1", state=MemberState.CHURNED)

    # 1 Reactivated (should count towards total but not have its own key in output based on current implementation)
    create_member(phone="8", name="React 1", state=MemberState.REACTIVATED)

    stats = service.get_stats()

    assert stats["total"] == 8
    assert stats["active"] == 2
    assert stats["new"] == 1
    assert stats["at_risk"] == 3
    assert stats["dormant"] == 0
    assert stats["churned"] == 1

    # Retention rate = (active / total) * 100 = (2 / 8) * 100 = 25.0
    assert stats["retention_rate"] == 25.0
