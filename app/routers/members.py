"""
Members Router - API endpoints for member management
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import date
from uuid import UUID

from app.database import get_db
from app.services.member_service import MemberService
from app.services.workout_service import WorkoutService
from app.services.diet_service import DietService
from app.models.member import MemberState, PrimaryGoal

router = APIRouter(prefix="/api/v1/members", tags=["Members"])


# ========== Pydantic Models ==========

class MemberCreate(BaseModel):
    phone: str = Field(..., description="WhatsApp number with country code")
    name: str = Field(..., min_length=2, max_length=100)
    age: Optional[int] = None
    gender: Optional[str] = None
    height_cm: Optional[int] = None
    current_weight_kg: Optional[float] = None
    target_weight_kg: Optional[float] = None
    primary_goal: Optional[str] = None
    dietary_preference: Optional[str] = None
    membership_start: Optional[date] = None
    membership_end: Optional[date] = None


class MemberUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    height_cm: Optional[int] = None
    current_weight_kg: Optional[float] = None
    target_weight_kg: Optional[float] = None
    primary_goal: Optional[str] = None
    dietary_preference: Optional[str] = None
    membership_end: Optional[date] = None


class CheckinCreate(BaseModel):
    weight_kg: Optional[float] = None
    energy_level: Optional[int] = Field(None, ge=1, le=5)
    diet_compliance: Optional[str] = None
    workouts_completed: Optional[int] = None


class MemberResponse(BaseModel):
    id: str
    phone: str
    name: str
    current_state: str
    streak_days: int
    onboarding_completed: bool
    membership_active: bool
    
    class Config:
        from_attributes = True


# ========== Endpoints ==========

@router.post("/", response_model=MemberResponse, status_code=201)
def create_member(member: MemberCreate, db: Session = Depends(get_db)):
    """Create a new gym member."""
    service = MemberService(db)
    
    # Check if already exists
    existing = service.get_by_phone(member.phone)
    if existing:
        raise HTTPException(status_code=400, detail="Member with this phone already exists")
    
    new_member = service.create(**member.model_dump())
    
    return MemberResponse(
        id=str(new_member.id),
        phone=new_member.phone,
        name=new_member.name,
        current_state=new_member.current_state.value,
        streak_days=new_member.streak_days,
        onboarding_completed=new_member.onboarding_completed,
        membership_active=new_member.is_membership_active()
    )


@router.get("/{phone}")
def get_member(phone: str, db: Session = Depends(get_db)):
    """Get member by phone number."""
    service = MemberService(db)
    member = service.get_by_phone(phone)
    
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Get current plans
    workout_service = WorkoutService(db)
    diet_service = DietService(db)
    
    current_workout = workout_service.get_current_plan(member.id)
    current_diet = diet_service.get_current_plan(member.id)
    progress = workout_service.get_progress_summary(member)
    
    return {
        "id": str(member.id),
        "phone": member.phone,
        "name": member.name,
        "age": member.age,
        "gender": member.gender.value if member.gender else None,
        "height_cm": member.height_cm,
        "current_weight_kg": member.current_weight_kg,
        "target_weight_kg": member.target_weight_kg,
        "primary_goal": member.primary_goal.value if member.primary_goal else None,
        "dietary_preference": member.dietary_preference.value if member.dietary_preference else None,
        "current_state": member.current_state.value,
        "streak_days": member.streak_days,
        "longest_streak": member.longest_streak,
        "onboarding_completed": member.onboarding_completed,
        "membership_start": member.membership_start.isoformat() if member.membership_start else None,
        "membership_end": member.membership_end.isoformat() if member.membership_end else None,
        "membership_active": member.is_membership_active(),
        "days_until_expiry": member.days_until_expiry(),
        "has_workout_plan": current_workout is not None,
        "has_diet_plan": current_diet is not None,
        "progress": progress
    }


@router.patch("/{phone}")
def update_member(phone: str, updates: MemberUpdate, db: Session = Depends(get_db)):
    """Update member information."""
    service = MemberService(db)
    member = service.get_by_phone(phone)
    
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Filter out None values
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    
    updated = service.update(member, **update_data)
    
    return {"message": "Member updated", "id": str(updated.id)}


@router.post("/{phone}/checkin")
async def record_checkin(phone: str, checkin: CheckinCreate, db: Session = Depends(get_db)):
    """Record a weekly check-in for a member."""
    member_service = MemberService(db)
    workout_service = WorkoutService(db)
    
    member = member_service.get_by_phone(phone)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Record check-in
    checkin_record = workout_service.record_checkin(
        member,
        weight_kg=checkin.weight_kg,
        energy_level=checkin.energy_level,
        diet_compliance=checkin.diet_compliance,
        workouts_completed=checkin.workouts_completed
    )
    
    # Get updated progress
    progress = workout_service.get_progress_summary(member)
    
    return {
        "message": "Check-in recorded",
        "checkin_id": str(checkin_record.id),
        "progress": progress
    }


@router.get("/{phone}/workout")
async def get_todays_workout(phone: str, db: Session = Depends(get_db)):
    """Get today's workout for a member."""
    member_service = MemberService(db)
    workout_service = WorkoutService(db)
    
    member = member_service.get_by_phone(phone)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    workout = workout_service.get_todays_workout(member)
    formatted = workout_service.format_workout_for_whatsapp(workout)
    
    return {
        "workout": workout,
        "formatted": formatted
    }


@router.post("/{phone}/workout/generate")
async def generate_workout_plan(phone: str, db: Session = Depends(get_db)):
    """Generate a new workout plan for a member."""
    member_service = MemberService(db)
    workout_service = WorkoutService(db)
    
    member = member_service.get_by_phone(phone)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Determine week number
    existing = workout_service.get_plan_history(member.id, limit=1)
    week_number = (existing[0].week_number + 1) if existing else 1
    
    plan = await workout_service.generate_plan(member, week_number=week_number)
    
    return {
        "message": "Workout plan generated",
        "plan_id": str(plan.id),
        "week_number": plan.week_number,
        "plan": plan.plan_json
    }


@router.get("/{phone}/diet")
def get_diet_plan(phone: str, db: Session = Depends(get_db)):
    """Get current diet plan for a member."""
    member_service = MemberService(db)
    diet_service = DietService(db)
    
    member = member_service.get_by_phone(phone)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    plan = diet_service.get_current_plan(member.id)
    formatted = diet_service.format_plan_for_whatsapp(plan)
    
    return {
        "plan": diet_service.get_plan_summary(plan),
        "formatted": formatted
    }


@router.post("/{phone}/diet/generate")
async def generate_diet_plan(phone: str, db: Session = Depends(get_db)):
    """Generate a new diet plan for a member."""
    member_service = MemberService(db)
    diet_service = DietService(db)
    
    member = member_service.get_by_phone(phone)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Determine week number
    current = diet_service.get_current_plan(member.id)
    week_number = (current.week_number + 1) if current else 1
    
    plan = await diet_service.generate_plan(member, week_number=week_number)
    
    return {
        "message": "Diet plan generated",
        "plan_id": str(plan.id),
        "calories": plan.daily_calories,
        "plan": plan.plan_json
    }


@router.get("/")
def list_members(
    state: Optional[str] = None,
    goal: Optional[str] = None,
    query: Optional[str] = None,
    limit: int = Query(50, le=100),
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List members with optional filters."""
    service = MemberService(db)
    
    state_enum = MemberState(state) if state else None
    goal_enum = PrimaryGoal(goal) if goal else None
    
    members = service.search(
        query=query,
        state=state_enum,
        goal=goal_enum,
        limit=limit,
        offset=offset
    )
    
    return {
        "count": len(members),
        "members": [
            {
                "id": str(m.id),
                "phone": m.phone,
                "name": m.name,
                "state": m.current_state.value,
                "streak": m.streak_days,
                "goal": m.primary_goal.value if m.primary_goal else None
            }
            for m in members
        ]
    }


@router.get("/stats/overview")
def get_member_stats(db: Session = Depends(get_db)):
    """Get member statistics overview."""
    service = MemberService(db)
    return service.get_stats()
