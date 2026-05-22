import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.member import Member, MemberState
from app.services.member_service import MemberService
from app.db_types import generate_uuid

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

def test_get_stats(db):
    # Arrange
    service = MemberService(db)

    # Create members in different states
    members = [
        Member(id=generate_uuid(), phone="1", name="A", current_state=MemberState.ACTIVE),
        Member(id=generate_uuid(), phone="2", name="B", current_state=MemberState.ACTIVE),
        Member(id=generate_uuid(), phone="3", name="C", current_state=MemberState.AT_RISK),
        Member(id=generate_uuid(), phone="4", name="D", current_state=MemberState.NEW),
        Member(id=generate_uuid(), phone="5", name="E", current_state=MemberState.NEW),
        Member(id=generate_uuid(), phone="6", name="F", current_state=MemberState.NEW),
    ]
    db.add_all(members)
    db.commit()

    # Act
    stats = service.get_stats()

    # Assert
    assert stats["total"] == 6
    assert stats["active"] == 2
    assert stats["at_risk"] == 1
    assert stats["new"] == 3
    assert stats["dormant"] == 0
    assert stats["churned"] == 0

    # Check retention rate: (2 / 6) * 100 = 33.333... -> 33.3
    assert stats["retention_rate"] == 33.3

def test_get_stats_empty(db):
    service = MemberService(db)
    stats = service.get_stats()

    assert stats["total"] == 0
    assert stats["active"] == 0
    assert stats["retention_rate"] == 0
