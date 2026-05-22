from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import pytest
from datetime import date

from app.main import app
from app.database import Base, get_db
from app.models.member import Member, MemberState, PrimaryGoal

# Setup in-memory SQLite DB for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(name="client")
def client_fixture():
    # Create tables
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as client:
        yield client
    # Drop tables
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(name="test_member")
def test_member_fixture():
    db = TestingSessionLocal()
    member = Member(
        phone="+1234567890",
        name="Test User",
        age=30,
        current_state=MemberState.ACTIVE,
        membership_start=date.today(),
        membership_end=date.today()
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    db.close()
    return member

def test_record_checkin(client, test_member):
    response = client.post(
        f"/api/v1/members/{test_member.phone}/checkin",
        json={
            "weight_kg": 75.0,
            "energy_level": 4,
            "workouts_completed": 3
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Check-in recorded"
    assert "checkin_id" in data
    assert "progress" in data
