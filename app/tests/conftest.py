import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import Member, WorkoutPlan, DietPlan, Class, ClassBooking, Message, Conversation, MemberPreferences

@pytest.fixture(scope="function")
def db_session():
    # Use in-memory SQLite database for speed
    engine = create_engine("sqlite:///:memory:")

    # Create tables
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()
