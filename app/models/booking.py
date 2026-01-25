"""
Class Booking Model - Gym class scheduling and booking
"""
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base
from app.db_types import GUID, StringArray, generate_uuid


class BookingStatus(str, Enum):
    """Booking lifecycle states"""
    BOOKED = "booked"
    WAITLIST = "waitlist"
    CANCELLED = "cancelled"
    ATTENDED = "attended"
    NO_SHOW = "no_show"


class ClassIntensity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Class(Base):
    """
    Gym class (Yoga, HIIT, Spin, etc.)
    Represents a scheduled class session.
    """
    __tablename__ = "classes"
    
    id = Column(GUID(), primary_key=True, default=generate_uuid)
    
    # Class details
    name = Column(String(100), nullable=False)  # e.g., "Morning Yoga", "HIIT Blast"
    description = Column(String(500), nullable=True)
    class_type = Column(String(50), nullable=False)  # yoga, hiit, spin, strength, dance
    
    # Trainer
    trainer_name = Column(String(100), nullable=False)
    trainer_id = Column(GUID(), nullable=True)  # Optional FK to trainers table
    
    # Schedule
    scheduled_at = Column(DateTime, nullable=False, index=True)
    duration_mins = Column(Integer, default=45)
    room = Column(String(50), nullable=True)  # e.g., "Studio A", "Main Floor"
    
    # Capacity
    capacity = Column(Integer, default=20)
    booked_count = Column(Integer, default=0)
    waitlist_count = Column(Integer, default=0)
    
    # Classification
    intensity = Column(String(20), default="medium")
    goal_tags = Column(StringArray(), nullable=True)  # ["weight_loss", "cardio", "flexibility"]
    suitable_for = Column(StringArray(), nullable=True)  # ["beginner", "intermediate"]
    
    # Status
    is_cancelled = Column(Boolean, default=False)
    cancellation_reason = Column(String(200), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    bookings = relationship("ClassBooking", back_populates="gym_class", lazy="dynamic")
    
    def __repr__(self):
        return f"<Class {self.name} at {self.scheduled_at}>"
    
    @property
    def available_slots(self) -> int:
        """Number of spots available"""
        return max(0, self.capacity - self.booked_count)
    
    @property
    def is_full(self) -> bool:
        """Check if class is at capacity"""
        return self.booked_count >= self.capacity
    
    def can_book(self) -> bool:
        """Check if new bookings are allowed"""
        if self.is_cancelled:
            return False
        if self.scheduled_at < datetime.utcnow():
            return False  # Class already started
        return not self.is_full


class ClassBooking(Base):
    """
    Member booking for a class.
    Tracks the full lifecycle: booked -> attended/no_show
    """
    __tablename__ = "class_bookings"
    
    id = Column(GUID(), primary_key=True, default=generate_uuid)
    member_id = Column(GUID(), ForeignKey("members.id"), nullable=False, index=True)
    class_id = Column(GUID(), ForeignKey("classes.id"), nullable=False, index=True)
    
    # Status
    status = Column(String(20), default=BookingStatus.BOOKED.value)
    waitlist_position = Column(Integer, nullable=True)  # Position if on waitlist
    
    # Reminders
    night_reminder_sent = Column(Boolean, default=False)
    morning_reminder_sent = Column(Boolean, default=False)
    
    # Timestamps
    booked_at = Column(DateTime, default=datetime.utcnow)
    cancelled_at = Column(DateTime, nullable=True)
    attended_at = Column(DateTime, nullable=True)
    
    # Relationships
    member = relationship("Member", back_populates="bookings")
    gym_class = relationship("Class", back_populates="bookings")
    
    def __repr__(self):
        return f"<ClassBooking {self.status} for class {self.class_id}>"
    
    def cancel(self):
        """Cancel the booking"""
        self.status = BookingStatus.CANCELLED.value
        self.cancelled_at = datetime.utcnow()
    
    def mark_attended(self):
        """Mark as attended"""
        self.status = BookingStatus.ATTENDED.value
        self.attended_at = datetime.utcnow()
    
    def mark_no_show(self):
        """Mark as no-show"""
        self.status = BookingStatus.NO_SHOW.value
