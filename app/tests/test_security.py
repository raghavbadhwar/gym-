from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import pytest

from app.main import app as fastapi_app
from app.database import Base, get_db
from app.config import settings
import app.models  # Register models

# In-memory database for testing
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

# Apply override
fastapi_app.dependency_overrides[get_db] = override_get_db

# Set test API key
settings.admin_api_key = "test-secret-key"

# Create tables
Base.metadata.create_all(bind=engine)

client = TestClient(fastapi_app)

def test_members_unauthorized():
    """Test accessing members endpoint without API key."""
    response = client.get("/api/v1/members/")
    assert response.status_code == 401
    assert response.json() == {"detail": "Missing API Key"}

def test_members_invalid_key():
    """Test accessing members endpoint with invalid API key."""
    response = client.get("/api/v1/members/", headers={"X-Admin-API-Key": "wrong-key"})
    assert response.status_code == 403
    assert response.json() == {"detail": "Invalid API Key"}

def test_members_authorized():
    """Test accessing members endpoint with valid API key."""
    response = client.get("/api/v1/members/", headers={"X-Admin-API-Key": settings.admin_api_key})
    assert response.status_code == 200
    # Should return a list (empty or not)
    assert "members" in response.json()

def test_classes_public_list():
    """Test accessing public classes list without API key."""
    response = client.get("/api/v1/classes/")
    assert response.status_code == 200
    assert "classes" in response.json()

def test_classes_create_unauthorized():
    """Test creating class without API key."""
    response = client.post(
        "/api/v1/classes/",
        json={
            "name": "Test Class",
            "class_type": "yoga",
            "trainer_name": "T",
            "scheduled_at": "2024-01-01T10:00:00"
        }
    )
    assert response.status_code == 401

def test_classes_create_authorized():
    """Test creating class with valid API key."""
    response = client.post(
        "/api/v1/classes/",
        headers={"X-Admin-API-Key": settings.admin_api_key},
        json={
            "name": "Test Class Secured",
            "class_type": "yoga",
            "trainer_name": "Trainer X",
            "scheduled_at": "2025-01-01T10:00:00",
            "duration_mins": 60,
            "capacity": 10
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Class Secured"
