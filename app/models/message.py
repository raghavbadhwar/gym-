"""
Message Model - WhatsApp conversation history
"""
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base
from app.db_types import GUID, JSONType, generate_uuid


class MessageDirection(str, Enum):
    """Message direction"""
    INBOUND = "inbound"   # From member to bot
    OUTBOUND = "outbound" # From bot to member


class MessageType(str, Enum):
    """WhatsApp message types"""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"
    INTERACTIVE = "interactive"  # Buttons/Lists
    TEMPLATE = "template"


class Message(Base):
    """
    WhatsApp message log.
    Stores all conversations for context and analytics.
    """
    __tablename__ = "messages"
    
    id = Column(GUID(), primary_key=True, default=generate_uuid)
    member_id = Column(GUID(), ForeignKey("members.id"), nullable=True, index=True)
    
    # WhatsApp identifiers
    wa_message_id = Column(String(100), nullable=True, unique=True)  # WhatsApp's message ID
    phone = Column(String(15), nullable=False, index=True)  # Sender/recipient phone
    
    # Direction
    direction = Column(String(10), nullable=False)  # inbound/outbound
    
    # Content
    message_type = Column(String(20), default=MessageType.TEXT.value)
    content = Column(Text, nullable=True)  # Text content
    media_url = Column(String(500), nullable=True)  # Media URL if applicable
    
    # For interactive messages
    payload = Column(JSONType(), nullable=True)
    """
    For buttons:
    {"type": "button", "button_id": "goal_weight_loss", "button_text": "Lose Weight"}
    
    For lists:
    {"type": "list", "row_id": "class_yoga_6am", "row_title": "Yoga 6 AM"}
    """
    
    # Processing
    intent = Column(String(50), nullable=True)  # Detected intent (book_class, check_progress, etc.)
    processed = Column(DateTime, nullable=True)  # When we processed this message
    
    # Status (for outbound)
    status = Column(String(20), nullable=True)  # sent, delivered, read, failed
    error = Column(Text, nullable=True)  # Error message if failed
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    member = relationship("Member", back_populates="messages")
    
    def __repr__(self):
        return f"<Message {self.direction} from {self.phone}>"


class ConversationState(Base):
    """
    Track conversation state for multi-step flows.
    E.g., onboarding flow, class booking flow.
    """
    __tablename__ = "conversation_states"
    
    id = Column(GUID(), primary_key=True, default=generate_uuid)
    phone = Column(String(15), nullable=False, unique=True, index=True)
    
    # Current flow
    current_flow = Column(String(50), nullable=True)  # onboarding, booking, checkin, etc.
    current_step = Column(String(50), nullable=True)  # Step within the flow
    
    # Flow data (temporary storage during multi-step flows)
    flow_data = Column(JSONType(), nullable=True)
    """
    Example for onboarding:
    {
        "name": "Rahul",
        "goal": "weight_loss",
        "diet_pref": "non_veg",
        "awaiting": "goal_selection"
    }
    """
    
    # Last activity
    last_message_at = Column(DateTime, default=datetime.utcnow)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ConversationState {self.phone} in {self.current_flow}>"
    
    def clear_flow(self):
        """Clear current flow state"""
        self.current_flow = None
        self.current_step = None
        self.flow_data = None
    
    def set_flow(self, flow: str, step: str, data: dict = None):
        """Set new flow state"""
        self.current_flow = flow
        self.current_step = step
        self.flow_data = data or {}
        self.last_message_at = datetime.utcnow()
