"""
Conversation Model - Store chat history for AI memory
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Boolean, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Conversation(Base):
    """Store conversation history for each member."""
    __tablename__ = "conversations"
    __table_args__ = (
        Index('ix_conversations_member_id_created_at', 'member_id', 'created_at'),
    )
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    member_id = Column(String(36), ForeignKey("members.id"), nullable=False)
    
    # Message details
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    message = Column(Text, nullable=False)
    intent = Column(String(50), nullable=True)  # Classified intent
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    member = relationship("Member", back_populates="conversations")
    
    def __repr__(self):
        return f"<Conversation {self.role}: {self.message[:30]}...>"


class MemberPreferences(Base):
    """Store learned preferences from conversations."""
    __tablename__ = "member_preferences"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    member_id = Column(String(36), ForeignKey("members.id"), nullable=False, unique=True)
    
    # Learned preferences
    preferred_workout_time = Column(String(20), nullable=True)  # morning, evening
    preferred_exercises = Column(Text, nullable=True)  # JSON list
    disliked_exercises = Column(Text, nullable=True)  # JSON list
    allergies = Column(Text, nullable=True)  # Food allergies
    favorite_foods = Column(Text, nullable=True)  # JSON list
    injuries = Column(Text, nullable=True)  # Any injuries to consider
    motivation_style = Column(String(50), nullable=True)  # gentle, intense, funny
    
    # Communication preferences
    prefers_hindi = Column(Boolean, default=False)
    response_length = Column(String(20), default="medium")  # short, medium, detailed
    
    # Activity patterns
    most_active_day = Column(String(20), nullable=True)
    avg_session_duration = Column(Integer, nullable=True)  # minutes
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    member = relationship("Member", back_populates="preferences")
