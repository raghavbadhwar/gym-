import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.config import settings
from app.database import Base, get_db

# Setup in-memory DB for tests
TEST_DATABASE_URL = "sqlite:///:memory:"

engine_test = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)

# Create tables in the test database
Base.metadata.create_all(bind=engine_test)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_members_unauthorized_no_header():
    """Verify that accessing members API without header fails"""
    original_key = settings.admin_api_key
    settings.admin_api_key = "test-key"
    try:
        response = client.get("/api/v1/members/")
        assert response.status_code == 401
        assert response.json() == {"detail": "Missing X-Admin-Key header"}
    finally:
        settings.admin_api_key = original_key

def test_members_unauthorized_wrong_header():
    """Verify that accessing members API with wrong key fails"""
    original_key = settings.admin_api_key
    settings.admin_api_key = "test-key"
    try:
        response = client.get("/api/v1/members/", headers={"X-Admin-Key": "wrong-key"})
        assert response.status_code == 401
        assert response.json() == {"detail": "Invalid API Key"}
    finally:
        settings.admin_api_key = original_key

def test_members_authorized():
    """Verify that accessing members API with correct key succeeds"""
    original_key = settings.admin_api_key
    settings.admin_api_key = "test-key"
    try:
        response = client.get("/api/v1/members/", headers={"X-Admin-Key": "test-key"})
        assert response.status_code == 200
        data = response.json()
        assert "members" in data
        assert "count" in data
    finally:
        settings.admin_api_key = original_key

def test_members_not_configured():
    """Verify that accessing members API when not configured returns 500"""
    original_key = settings.admin_api_key
    settings.admin_api_key = "" # Ensure empty
    try:
        response = client.get("/api/v1/members/", headers={"X-Admin-Key": "any-key"})
        assert response.status_code == 500
        assert response.json() == {"detail": "Admin API not configured"}
    finally:
        settings.admin_api_key = original_key
