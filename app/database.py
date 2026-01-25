"""
Database connection and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator

from app.config import settings

# Create engine - SQLite-compatible settings
if settings.database_url.startswith("sqlite"):
    # SQLite doesn't support connection pooling the same way
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},  # Allow multi-threaded access
        echo=settings.app_env == "development"
    )
else:
    # PostgreSQL with connection pooling
    engine = create_engine(
        settings.database_url,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        echo=settings.app_env == "development"
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI routes to get database session.
    Automatically closes session after request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for getting database session outside of request context.
    Use for background tasks, cron jobs, etc.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    # Import all models so they are registered with Base
    from app.models import member, workout, diet, booking, message
    Base.metadata.create_all(bind=engine)
