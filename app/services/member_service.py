"""
Member Service - Member management and state tracking

Handles member CRUD operations, state management, 
escalation marking, and conversation logging.
"""
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from loguru import logger

from app.models.member import Member, MemberState, PrimaryGoal, DietaryPreference, Gender
from app.models.message import ConversationState, Message


class MemberService:
    """
    Service for member management operations.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_phone(self, phone: str) -> Optional[Member]:
        """Get member by phone number."""
        # Normalize phone number (remove + and spaces)
        normalized = phone.replace("+", "").replace(" ", "").strip()
        return self.db.query(Member).filter(
            Member.phone.in_([phone, normalized, f"+{normalized}"])
        ).first()
    
    def get_by_id(self, member_id: UUID) -> Optional[Member]:
        """Get member by ID."""
        return self.db.query(Member).filter(Member.id == member_id).first()
    
    def create(
        self,
        phone: str,
        name: str,
        membership_start: date = None,
        membership_end: date = None,
        **kwargs
    ) -> Member:
        """
        Create a new member.
        
        Args:
            phone: WhatsApp phone number (with country code)
            name: Member's name
            membership_start: Start date of membership
            membership_end: End date of membership
            **kwargs: Additional member attributes
        """
        # Normalize phone
        phone = phone.replace("+", "").replace(" ", "").strip()
        
        member = Member(
            phone=phone,
            name=name,
            membership_start=membership_start or date.today(),
            membership_end=membership_end or (date.today() + timedelta(days=365)),
            current_state=MemberState.NEW,
            **kwargs
        )
        
        self.db.add(member)
        self.db.commit()
        self.db.refresh(member)
        
        logger.info(f"Created new member: {member.name} ({member.phone})")
        return member
    
    def update(self, member: Member, **kwargs) -> Member:
        """Update member attributes."""
        for key, value in kwargs.items():
            if hasattr(member, key):
                setattr(member, key, value)
        
        member.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(member)
        return member
    
    def update_state(self, member: Member, new_state: MemberState, reason: str = None):
        """
        Update member's engagement state.
        
        State transitions:
        - NEW -> ACTIVE (after first workout or 7 days)
        - ACTIVE -> AT_RISK (no visit 7+ days)
        - AT_RISK -> DORMANT (no visit 14+ days)
        - DORMANT -> CHURNED (no visit 30+ days)
        - ANY -> ACTIVE (on workout/check-in)
        - CHURNED -> REACTIVATED (on return)
        """
        old_state = member.current_state
        member.current_state = new_state
        member.updated_at = datetime.utcnow()
        
        self.db.commit()
        logger.info(f"Member {member.phone} state: {old_state} -> {new_state} ({reason})")
    
    def record_activity(self, member: Member, activity_type: str = "workout"):
        """
        Record member activity (workout, check-in, class attendance).
        Updates state and streak accordingly.
        """
        today = date.today()
        
        # Update streak for workouts
        if activity_type == "workout":
            member.update_streak(workout_today=True)
        
        # Update last activity
        member.last_workout_date = today
        member.last_message_date = datetime.utcnow()
        
        # Reactivate if was dormant/churned
        if member.current_state in [MemberState.DORMANT, MemberState.CHURNED]:
            member.current_state = MemberState.REACTIVATED
        elif member.current_state in [MemberState.NEW, MemberState.AT_RISK]:
            member.current_state = MemberState.ACTIVE
        
        self.db.commit()
    
    def complete_onboarding(
        self,
        member: Member,
        goal: str,
        dietary_pref: str,
        weight: float = None,
        target_weight: float = None,
        height: int = None,
        age: int = None,
        gender: str = None
    ) -> Member:
        """
        Complete the onboarding process for a member.
        """
        member.primary_goal = PrimaryGoal(goal) if goal else None
        member.dietary_preference = DietaryPreference(dietary_pref) if dietary_pref else None
        member.current_weight_kg = weight
        member.target_weight_kg = target_weight
        member.height_cm = height
        member.age = age
        member.gender = Gender(gender) if gender else None
        member.onboarding_completed = True
        member.onboarding_step = "completed"
        
        self.db.commit()
        self.db.refresh(member)
        
        logger.success(f"✅ Completed onboarding for {member.phone}")
        return member
    
    def mark_for_escalation(self, phone: str, reason: str):
        """
        Mark a member for escalation to human manager.
        
        Args:
            phone: Member's phone number
            reason: Reason for escalation
        """
        phone = phone.replace("+", "").replace(" ", "").strip()
        member = self.get_by_phone(phone)
        
        if member:
            # Update onboarding step to indicate escalation
            member.onboarding_step = f"ESCALATE: {reason}"
            member.updated_at = datetime.utcnow()
            self.db.commit()
            logger.warning(f"⚠️ Member {phone} marked for escalation: {reason}")
        else:
            # Create a conversation state entry for non-members
            state = self.get_conversation_state(phone)
            if state:
                state.flow_data = state.flow_data or {}
                state.flow_data["escalation_reason"] = reason
                state.current_flow = "escalated"
            else:
                state = ConversationState(
                    phone=phone,
                    current_flow="escalated",
                    current_step="pending",
                    flow_data={"escalation_reason": reason}
                )
                self.db.add(state)
            self.db.commit()
            logger.warning(f"⚠️ Non-member {phone} escalation logged: {reason}")
    
    def log_message(
        self,
        phone: str,
        content: str,
        direction: str,
        intent: str = None,
        message_type: str = "text"
    ) -> Message:
        """
        Log a message to the conversation history.
        
        Args:
            phone: Phone number
            content: Message content
            direction: 'inbound' or 'outbound'
            intent: Detected intent (optional)
            message_type: Message type (text, image, etc.)
        """
        phone = phone.replace("+", "").replace(" ", "").strip()
        member = self.get_by_phone(phone)
        
        message = Message(
            member_id=member.id if member else None,
            phone=phone,
            direction=direction,
            content=content,
            intent=intent,
            message_type=message_type,
            processed=datetime.utcnow()
        )
        
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        
        logger.debug(f"💬 Logged {direction} message from {phone}: {content[:30]}...")
        return message
    
    def get_at_risk_members(self, days: int = 7) -> List[Member]:
        """Get members who haven't worked out in X days."""
        cutoff = date.today() - timedelta(days=days)
        return self.db.query(Member).filter(
            and_(
                Member.last_workout_date < cutoff,
                Member.current_state.in_([MemberState.ACTIVE, MemberState.AT_RISK])
            )
        ).all()
    
    def get_expiring_memberships(self, days: int = 7) -> List[Member]:
        """Get members whose membership expires in X days."""
        today = date.today()
        cutoff = today + timedelta(days=days)
        return self.db.query(Member).filter(
            and_(
                Member.membership_end >= today,
                Member.membership_end <= cutoff
            )
        ).all()
    
    def get_new_members(self, days: int = 7) -> List[Member]:
        """Get members who joined in the last X days."""
        cutoff = date.today() - timedelta(days=days)
        return self.db.query(Member).filter(
            Member.created_at >= cutoff
        ).all()
    
    def search(
        self,
        query: str = None,
        state: MemberState = None,
        goal: PrimaryGoal = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Member]:
        """Search members with filters."""
        q = self.db.query(Member)
        
        if query:
            q = q.filter(
                Member.name.ilike(f"%{query}%") |
                Member.phone.ilike(f"%{query}%")
            )
        
        if state:
            q = q.filter(Member.current_state == state)
        
        if goal:
            q = q.filter(Member.primary_goal == goal)
        
        return q.offset(offset).limit(limit).all()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get member statistics for dashboard."""
        # Optimize to single query using group by
        # Returns list of (state, count) tuples
        stats_query = self.db.query(
            Member.current_state,
            func.count(Member.id)
        ).group_by(Member.current_state).all()

        # Convert to dictionary
        stats_map = {state: count for state, count in stats_query}

        # Helper to safely get count
        def get_count(state):
            return stats_map.get(state, 0)

        active = get_count(MemberState.ACTIVE)
        at_risk = get_count(MemberState.AT_RISK)
        dormant = get_count(MemberState.DORMANT)
        churned = get_count(MemberState.CHURNED)
        new = get_count(MemberState.NEW)

        # Total is sum of all states
        total = sum(stats_map.values())
        
        return {
            "total": total,
            "active": active,
            "at_risk": at_risk,
            "dormant": dormant,
            "churned": churned,
            "new": new,
            "retention_rate": round((active / total) * 100, 1) if total > 0 else 0
        }
    
    def get_conversation_history(
        self,
        phone: str,
        limit: int = 20
    ) -> List[Message]:
        """Get recent conversation history for a member."""
        phone = phone.replace("+", "").replace(" ", "").strip()
        return self.db.query(Message).filter(
            Message.phone == phone
        ).order_by(Message.created_at.desc()).limit(limit).all()
    
    # Conversation State Management
    def get_conversation_state(self, phone: str) -> Optional[ConversationState]:
        """Get current conversation state for a phone number."""
        phone = phone.replace("+", "").replace(" ", "").strip()
        return self.db.query(ConversationState).filter(
            ConversationState.phone == phone
        ).first()
    
    def set_conversation_state(
        self,
        phone: str,
        flow: str,
        step: str,
        data: dict = None
    ) -> ConversationState:
        """Set or update conversation state."""
        phone = phone.replace("+", "").replace(" ", "").strip()
        state = self.get_conversation_state(phone)
        
        if state:
            state.current_flow = flow
            state.current_step = step
            state.flow_data = data or {}
            state.last_message_at = datetime.utcnow()
        else:
            state = ConversationState(
                phone=phone,
                current_flow=flow,
                current_step=step,
                flow_data=data or {}
            )
            self.db.add(state)
        
        self.db.commit()
        self.db.refresh(state)
        return state
    
    def clear_conversation_state(self, phone: str):
        """Clear conversation state after flow completion."""
        state = self.get_conversation_state(phone)
        if state:
            state.clear_flow()
            self.db.commit()

