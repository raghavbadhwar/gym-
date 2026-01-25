"""
Member Model - Core user data and state tracking
"""
import uuid
from datetime import datetime, date
from enum import Enum
from sqlalchemy import Column, String, Integer, Date, DateTime, Enum as SQLEnum, Float, Boolean
from sqlalchemy.orm import relationship

from app.database import Base
from app.db_types import GUID, generate_uuid


class MemberState(str, Enum):
    """Member engagement states - tracks lifecycle"""
    NEW = "new"           # Just joined (0-7 days)
    ACTIVE = "active"     # Regular engagement
    AT_RISK = "at_risk"   # No visit 7+ days
    DORMANT = "dormant"   # No visit 14+ days
    CHURNED = "churned"   # No visit 30+ days
    REACTIVATED = "reactivated"  # Returned after churning


class PrimaryGoal(str, Enum):
    """Fitness goals"""
    WEIGHT_LOSS = "weight_loss"
    MUSCLE_GAIN = "muscle_gain"
    GENERAL_FITNESS = "general_fitness"
    STRENGTH = "strength"
    ENDURANCE = "endurance"


class DietaryPreference(str, Enum):
    """Dietary preferences for meal plans"""
    VEG = "veg"
    NON_VEG = "non_veg"
    EGGETARIAN = "eggetarian"
    VEGAN = "vegan"


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class Member(Base):
    """
    Gym member profile with all personal data, 
    fitness goals, and engagement tracking.
    """
    __tablename__ = "members"
    
    # Primary key
    id = Column(GUID(), primary_key=True, default=generate_uuid)
    
    # Contact info (phone is unique - used for WhatsApp)
    phone = Column(String(15), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=True)
    
    # Physical attributes
    age = Column(Integer, nullable=True)
    gender = Column(SQLEnum(Gender), nullable=True)
    height_cm = Column(Integer, nullable=True)
    current_weight_kg = Column(Float, nullable=True)
    target_weight_kg = Column(Float, nullable=True)
    
    # Fitness goals
    primary_goal = Column(SQLEnum(PrimaryGoal), nullable=True)
    dietary_preference = Column(SQLEnum(DietaryPreference), nullable=True)
    experience_level = Column(String(20), default="beginner")  # beginner/intermediate/advanced
    
    # Engagement tracking
    current_state = Column(SQLEnum(MemberState), default=MemberState.NEW)
    streak_days = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_workout_date = Column(Date, nullable=True)
    last_checkin_date = Column(Date, nullable=True)
    last_message_date = Column(DateTime, nullable=True)
    
    # Onboarding status
    onboarding_completed = Column(Boolean, default=False)
    onboarding_step = Column(String(50), default="welcome")
    
    # Membership
    membership_start = Column(Date, nullable=True)
    membership_end = Column(Date, nullable=True)
    membership_type = Column(String(50), nullable=True)  # monthly/quarterly/annual
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    workout_plans = relationship("WorkoutPlan", back_populates="member", lazy="dynamic")
    diet_plans = relationship("DietPlan", back_populates="member", lazy="dynamic")
    bookings = relationship("ClassBooking", back_populates="member", lazy="dynamic")
    messages = relationship("Message", back_populates="member", lazy="dynamic")
    conversations = relationship("Conversation", back_populates="member", lazy="dynamic")
    preferences = relationship("MemberPreferences", back_populates="member", uselist=False)
    
    def __repr__(self):
        return f"<Member {self.name} ({self.phone})>"
    
    def is_membership_active(self) -> bool:
        """Check if membership is currently active"""
        if not self.membership_end:
            return False
        return date.today() <= self.membership_end
    
    def days_until_expiry(self) -> int:
        """Days until membership expires"""
        if not self.membership_end:
            return 0
        delta = self.membership_end - date.today()
        return max(0, delta.days)
    
    def update_streak(self, workout_today: bool = True):
        """Update workout streak"""
        today = date.today()
        if workout_today:
            if self.last_workout_date == today:
                return  # Already updated today
            
            if self.last_workout_date and (today - self.last_workout_date).days == 1:
                # Consecutive day
                self.streak_days += 1
            else:
                # Streak broken, start fresh
                self.streak_days = 1
            
            self.last_workout_date = today
            self.longest_streak = max(self.longest_streak, self.streak_days)
