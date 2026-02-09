from fastapi.testclient import TestClient
from app.main import app
from app.config import get_settings, Settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base, get_db

# Use an in-memory SQLite database for testing with StaticPool to persist data
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Import models so they are registered with Base
from app.models import member, workout, diet, booking, message

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Override the database dependency
app.dependency_overrides[get_db] = override_get_db

# Override settings to ensure we use the test API key
def override_get_settings():
    return Settings(
        admin_api_key="secret-admin-key",
        database_url=SQLALCHEMY_DATABASE_URL,
        app_env="testing"
    )

app.dependency_overrides[get_settings] = override_get_settings

client = TestClient(app)

def test_read_members_no_auth():
    """
    Test that the members endpoint is protected (returns 401 without auth).
    """
    response = client.get("/api/v1/members/")
    assert response.status_code == 401
    assert response.json()["detail"] == "Admin API Key missing"

def test_read_members_invalid_auth():
    """
    Test that the members endpoint rejects invalid keys.
    """
    response = client.get(
        "/api/v1/members/",
        headers={"X-Admin-Key": "wrong-key"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid Admin API Key"

def test_read_members_valid_auth():
    """
    Test that the members endpoint accepts the correct key.
    """
    # Uses the default key set in override_get_settings
    response = client.get(
        "/api/v1/members/",
        headers={"X-Admin-Key": "secret-admin-key"}
    )
    assert response.status_code == 200
