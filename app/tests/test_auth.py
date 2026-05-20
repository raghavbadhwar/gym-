import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.config import settings, get_settings, Settings
from app.database import Base, get_db

# Override settings to provide a test API key
def override_get_settings():
    return Settings(admin_api_key="test-secret-key")

app.dependency_overrides[get_settings] = override_get_settings

# Setup in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite://"

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

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    # Import all models to ensure they are registered
    # (This might be redundant if they are imported in app/database.py's init_db but safer here)
    from app.models import member

    # Create tables
    Base.metadata.create_all(bind=engine)
    yield
    # Drop tables
    Base.metadata.drop_all(bind=engine)

def test_members_unauthorized_without_key():
    response = client.get("/api/v1/members/")
    assert response.status_code == 403
    assert response.json() == {"detail": "Missing API Key"}

def test_members_unauthorized_with_wrong_key():
    response = client.get("/api/v1/members/", headers={"X-Admin-Key": "wrong-key"})
    assert response.status_code == 403
    assert response.json() == {"detail": "Invalid API Key"}

def test_members_authorized_with_correct_key():
    # Use the test key defined in the override
    headers = {"X-Admin-Key": "test-secret-key"}
    response = client.get("/api/v1/members/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "count" in data
    assert "members" in data
