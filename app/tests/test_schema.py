import pytest
from sqlalchemy import create_engine, inspect
from app.database import Base
from app.models.conversation import Conversation
# Import Member to ensure FK target table exists
from app.models.member import Member

DATABASE_URL = "sqlite:///:memory:"

def test_conversation_composite_index():
    """Verify that the composite index on (member_id, created_at) exists."""
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    indexes = inspector.get_indexes("conversations")

    # Find the composite index
    composite_idx = next(
        (idx for idx in indexes if idx["name"] == "ix_conversation_member_created"),
        None
    )

    assert composite_idx is not None, "Composite index 'ix_conversation_member_created' is missing"
    assert composite_idx["column_names"] == ["member_id", "created_at"], \
        f"Index columns mismatch. Expected ['member_id', 'created_at'], got {composite_idx['column_names']}"

    # Verify redundant single-column index on member_id is gone
    # Default naming for index=True on member_id would be 'ix_conversations_member_id'
    member_idx = next(
        (idx for idx in indexes if idx["name"] == "ix_conversations_member_id"),
        None
    )

    assert member_idx is None, "Redundant index 'ix_conversations_member_id' should not exist"

    # Verify created_at is still indexed (we kept index=True)
    created_at_idx = next(
        (idx for idx in indexes if idx["column_names"] == ["created_at"]),
        None
    )
    assert created_at_idx is not None, "Index on 'created_at' should strictly exist"
