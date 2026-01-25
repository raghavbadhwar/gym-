"""
Models package - imports all models for easy access
"""
from app.models.member import Member, MemberState
from app.models.workout import WorkoutPlan
from app.models.diet import DietPlan
from app.models.booking import Class, ClassBooking, BookingStatus
from app.models.message import Message, MessageDirection
from app.models.conversation import Conversation, MemberPreferences

__all__ = [
    "Member", "MemberState",
    "WorkoutPlan",
    "DietPlan", 
    "Class", "ClassBooking", "BookingStatus",
    "Message", "MessageDirection",
    "Conversation", "MemberPreferences"
]

