"""
Chat Router - Real-time AI chat endpoint for demo and testing

This provides a simple chat API that:
1. Creates or retrieves member by phone
2. Uses their full profile (preferences, weight, height, goals)
3. Calls real Gemini AI with personalized context
4. Stores conversation history
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
import json
import re

from app.database import get_db
from app.services.member_service import MemberService
from app.services.workout_service import WorkoutService
from app.services.diet_service import DietService
from app.services.ai_service import ai_service
from app.services.ai_engine import ai_engine, Intent
from app.models.conversation import Conversation
from app.config import settings
from loguru import logger

router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])


# ========== Pydantic Models ==========

class ChatMessage(BaseModel):
    """Incoming chat message."""
    phone: str = Field(..., description="User's phone number")
    message: str = Field(..., description="User's message")
    name: Optional[str] = Field(default="Demo User", description="User's name")


class ChatResponse(BaseModel):
    """Chat response with member context."""
    response: str
    member_id: Optional[str] = None
    member_name: Optional[str] = None
    intent: Optional[str] = None
    is_new_member: bool = False
    member_context: Optional[Dict[str, Any]] = None


class MemberOnboard(BaseModel):
    """Quick onboarding data."""
    phone: str
    name: str
    age: Optional[int] = 25
    gender: Optional[str] = "male"
    height_cm: Optional[int] = 170
    current_weight_kg: Optional[float] = 70
    target_weight_kg: Optional[float] = 70
    primary_goal: Optional[str] = "general_fitness"  # weight_loss, muscle_gain, general_fitness
    dietary_preference: Optional[str] = "non_veg"  # veg, non_veg, eggetarian


# ========== Sync Helper Functions ==========

def _get_initial_context_sync(chat: ChatMessage, db: Session):
    """
    Synchronously load member, context, and plans.
    """
    member_service = MemberService(db)
    workout_service = WorkoutService(db)
    diet_service = DietService(db)
    
    # Get or create member
    member = member_service.get_by_phone(chat.phone)
    is_new = False
    
    if not member:
        # Create new member with name from message or default
        member = member_service.create(
            phone=chat.phone,
            name=chat.name or "New Member"
        )
        is_new = True
        logger.info(f"Created new member: {chat.phone}")
    
    # Extract name from message patterns like "hi i am raghav" or "my name is priya"
    name_patterns = [
        r"(?:i am|i'm|my name is|this is|call me)\s+([a-zA-Z]+)",
        r"^([a-zA-Z]+)\s+here$",
    ]
    extracted_name = None
    for pattern in name_patterns:
        match = re.search(pattern, chat.message.lower())
        if match:
            extracted_name = match.group(1).capitalize()
            break
    
    # Update member name if we extracted one or if chat.name is provided
    if extracted_name and extracted_name != member.name:
        logger.info(f"Updating member name from '{member.name}' to '{extracted_name}'")
        member.name = extracted_name
        db.commit()
    elif chat.name and chat.name != "Demo User" and chat.name != member.name:
        logger.info(f"Updating member name from '{member.name}' to '{chat.name}'")
        member.name = chat.name
        db.commit()
    
    # Load conversation history (last 10 messages)
    conversation_history = db.query(Conversation).filter(
        Conversation.member_id == str(member.id)
    ).order_by(Conversation.created_at.desc()).limit(10).all()
    
    # Format history for AI context
    history_text = ""
    if conversation_history:
        history_items = []
        for conv in reversed(conversation_history):  # Oldest first
            role = "Member" if conv.role == "user" else "GymBuddy"
            history_items.append(f"{role}: {conv.message[:100]}...")
        history_text = "\n".join(history_items[-5:])  # Last 5 exchanges
    else:
        history_text = "No previous conversation - this is their first message!"
    
    # Build full member context
    member_context = {
        "name": member.name,
        "phone": member.phone,
        "age": member.age,
        "gender": member.gender.value if member.gender else None,
        "height_cm": member.height_cm,
        "current_weight_kg": member.current_weight_kg,
        "target_weight_kg": member.target_weight_kg,
        "primary_goal": member.primary_goal.value if member.primary_goal else None,
        "dietary_preference": member.dietary_preference.value if member.dietary_preference else None,
        "streak_days": member.streak_days,
        "longest_streak": member.longest_streak,
        "onboarding_completed": member.onboarding_completed,
        "membership_active": member.is_membership_active(),
        "conversation_history": history_text
    }
    
    # Get current plans if they exist
    try:
        current_workout = workout_service.get_current_plan(member.id)
        current_diet = diet_service.get_current_plan(member.id)
        progress = workout_service.get_progress_summary(member)
        
        member_context["has_workout_plan"] = current_workout is not None
        member_context["has_diet_plan"] = current_diet is not None
        member_context["progress"] = progress
    except Exception as e:
        logger.warning(f"Could not load plans: {e}")

    return member, is_new, member_context

def _save_message_sync(db: Session, member_id: str, role: str, message: str, intent: str):
    """Synchronously save a message to conversation history."""
    conv = Conversation(
        member_id=member_id,
        role=role,
        message=message,
        intent=intent
    )
    db.add(conv)
    if role == "assistant":
        db.commit()


# ========== Endpoints ==========

@router.post("/message", response_model=ChatResponse)
async def send_chat_message(chat: ChatMessage, db: Session = Depends(get_db)):
    """
    Send a chat message and get AI-powered personalized response.

    This endpoint:
    1. Looks up or creates the member
    2. Retrieves their full profile and progress
    3. Loads conversation history for context
    4. Classifies intent using AI
    5. Generates personalized response with real AI
    6. Saves conversation to history
    """
    
    # 1. Run synchronous member loading in threadpool
    member, is_new, member_context = await run_in_threadpool(
        _get_initial_context_sync, chat, db
    )

    # 2. Classify intent (Async)
    intent_result = await ai_engine.classify_intent(chat.message, is_new_user=is_new)
    intent = intent_result.get("intent", Intent.GENERAL)
    
    logger.info(f"Intent: {intent.value}, Confidence: {intent_result.get('confidence', 0)}")
    
    # 3. Save user message (Sync in threadpool)
    await run_in_threadpool(
        _save_message_sync, db, str(member.id), "user", chat.message, intent.value
    )
    
    # 4. Handle intent (Async wrapper around mixed logic)
    workout_service = WorkoutService(db)
    diet_service = DietService(db)

    response = await _handle_intent(
        intent=intent,
        message=chat.message,
        member=member,
        member_context=member_context,
        workout_service=workout_service,
        diet_service=diet_service,
        db=db
    )
    
    # 5. Save assistant response (Sync in threadpool)
    await run_in_threadpool(
        _save_message_sync, db, str(member.id), "assistant", response[:500], intent.value
    )
    
    return ChatResponse(
        response=response,
        member_id=str(member.id),
        member_name=member.name,
        intent=intent.value,
        is_new_member=is_new,
        member_context=member_context
    )


@router.post("/onboard")
async def quick_onboard(data: MemberOnboard, db: Session = Depends(get_db)):
    """
    Quick onboard a member with their preferences.
    
    Creates or updates member profile with all their details,
    then generates personalized workout and diet plans.
    """
    member_service = MemberService(db)
    workout_service = WorkoutService(db)
    diet_service = DietService(db)
    
    # Get or create member
    member = member_service.get_by_phone(data.phone)
    
    if member:
        # Update existing
        member = member_service.update(
            member,
            name=data.name,
            age=data.age,
            gender=data.gender,
            height_cm=data.height_cm,
            current_weight_kg=data.current_weight_kg,
            target_weight_kg=data.target_weight_kg,
            primary_goal=data.primary_goal,
            dietary_preference=data.dietary_preference
        )
        is_new = False
    else:
        # Create new
        member = member_service.create(
            phone=data.phone,
            name=data.name,
            age=data.age,
            gender=data.gender,
            height_cm=data.height_cm,
            current_weight_kg=data.current_weight_kg,
            target_weight_kg=data.target_weight_kg,
            primary_goal=data.primary_goal,
            dietary_preference=data.dietary_preference
        )
        is_new = True
    
    # Mark onboarding complete
    member.onboarding_completed = True
    db.commit()
    
    # Generate plans
    try:
        workout_plan = await workout_service.generate_plan(member, week_number=1)
        diet_plan = await diet_service.generate_plan(member, week_number=1)
        plans_generated = True
    except Exception as e:
        logger.error(f"Failed to generate plans: {e}")
        workout_plan = None
        diet_plan = None
        plans_generated = False
    
    return {
        "message": "Member onboarded successfully!",
        "member_id": str(member.id),
        "is_new": is_new,
        "plans_generated": plans_generated,
        "profile": {
            "name": member.name,
            "goal": data.primary_goal,
            "dietary_preference": data.dietary_preference,
            "current_weight": data.current_weight_kg,
            "target_weight": data.target_weight_kg
        }
    }


@router.get("/member/{phone}")
async def get_member_context(phone: str, db: Session = Depends(get_db)):
    """Get full member context for chat."""
    member_service = MemberService(db)
    workout_service = WorkoutService(db)
    diet_service = DietService(db)
    
    member = member_service.get_by_phone(phone)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Get current plans
    current_workout = workout_service.get_current_plan(member.id)
    current_diet = diet_service.get_current_plan(member.id)
    progress = workout_service.get_progress_summary(member)
    
    return {
        "member": {
            "id": str(member.id),
            "name": member.name,
            "phone": member.phone,
            "age": member.age,
            "gender": member.gender.value if member.gender else None,
            "height_cm": member.height_cm,
            "current_weight_kg": member.current_weight_kg,
            "target_weight_kg": member.target_weight_kg,
            "primary_goal": member.primary_goal.value if member.primary_goal else None,
            "dietary_preference": member.dietary_preference.value if member.dietary_preference else None,
            "streak_days": member.streak_days,
            "longest_streak": member.longest_streak,
            "onboarding_completed": member.onboarding_completed
        },
        "workout_plan": workout_service.get_plan_summary(current_workout) if current_workout else None,
        "diet_plan": diet_service.get_plan_summary(current_diet) if current_diet else None,
        "progress": progress
    }


async def _handle_intent(
    intent: Intent,
    message: str,
    member,
    member_context: Dict[str, Any],
    workout_service: WorkoutService,
    diet_service: DietService,
    db: Session
) -> str:
    """Handle specific intents with real member data."""
    
    # ===== WORKOUT =====
    if intent == Intent.WORKOUT:
        # Check if member has a workout plan
        current_plan = await run_in_threadpool(workout_service.get_current_plan, member.id)
        
        if not current_plan:
            # Generate new plan with AI
            logger.info(f"Generating new workout plan for {member.name}")
            plan = await workout_service.generate_plan(member, week_number=1)
            todays_workout = await run_in_threadpool(workout_service.get_todays_workout, member)
            return workout_service.format_workout_for_whatsapp(todays_workout)
        else:
            # Return today's workout from existing plan
            todays_workout = await run_in_threadpool(workout_service.get_todays_workout, member)
            return workout_service.format_workout_for_whatsapp(todays_workout)
    
    # ===== DIET =====
    elif intent == Intent.DIET:
        current_plan = await run_in_threadpool(diet_service.get_current_plan, member.id)
        
        if not current_plan:
            # Generate new diet plan with AI
            logger.info(f"Generating new diet plan for {member.name}")
            plan = await diet_service.generate_plan(member, week_number=1)
            return diet_service.format_plan_for_whatsapp(plan)
        else:
            return diet_service.format_plan_for_whatsapp(current_plan)
    
    # ===== PROGRESS =====
    elif intent == Intent.PROGRESS:
        progress = await run_in_threadpool(workout_service.get_progress_summary, member)
        diet_trend = None
        if member.current_weight_kg:
             diet_trend = await run_in_threadpool(diet_service.get_weight_trend, member)
        
        lines = [
            f"📊 *Progress Report for {member.name}*",
            "═══════════════════════",
            "",
            f"🔥 *Current Streak:* {member.streak_days} days",
            f"🏆 *Best Streak:* {member.longest_streak} days",
        ]
        
        if member.current_weight_kg:
            lines.append(f"\n⚖️ *Weight:* {member.current_weight_kg} kg")
            if member.target_weight_kg:
                diff = abs(member.current_weight_kg - member.target_weight_kg)
                lines.append(f"🎯 *Target:* {member.target_weight_kg} kg ({diff:.1f} kg to go)")
        
        if diet_trend:
            lines.append(f"\n📈 *Trend:* {diet_trend.get('message', 'Keep going!')}")
        
        if progress:
            lines.append(f"\n💪 *Workouts this week:* {progress.get('workouts_this_week', 0)}")
        
        lines.extend([
            "",
            "Keep pushing! You're doing amazing! 💪"
        ])
        
        return "\n".join(lines)
    
    # ===== GREETING =====
    elif intent in [Intent.GREETING, Intent.NEW_LEAD]:
        goal_text = ""
        if member.primary_goal:
            goals = {
                "weight_loss": "lose weight",
                "muscle_gain": "build muscle", 
                "general_fitness": "stay fit"
            }
            goal_text = f" I see you're working to {goals.get(member.primary_goal.value, 'stay healthy')}!"
        
        return f"""👋 Hey {member.name}! Welcome to *{settings.gym_name}*!{goal_text}

I'm GymBuddy, your AI fitness assistant. I remember everything about you and create personalized plans!

What would you like today?
• *workout* - Get your personalized workout
• *diet* - See your meal plan  
• *progress* - Check your stats
• *help* - See all commands

Just type what you need! 💪"""
    
    # ===== HUMAN HELP =====
    elif intent == Intent.HUMAN_HELP:
        return """🙏 I understand you'd like to speak with someone.

Our gym manager will contact you shortly at your number.

In the meantime, is there anything else I can help with?"""
    
    # ===== GENERAL / FAQ / CONVERSATIONAL =====
    else:
        # Use REAL AI to generate intelligent response with full context
        # This handles: FAQ, GENERAL, OFF_TOPIC, CANCEL, and any conversational messages
        
        # Build progress summary
        progress_text = "No progress data yet"
        if member_context.get("progress"):
            p = member_context["progress"]
            progress_text = f"Streak: {p.get('current_streak', 0)} days, Weight change: {p.get('weight_change', 0)} kg"
        
        response = await ai_engine.generate_response(
            message=message,
            intent=intent,
            context={
                "member_name": member.name,
                "member_goal": member.primary_goal.value if member.primary_goal else "not set yet - ask them!",
                "weight": member.current_weight_kg or "not provided",
                "target_weight": member.target_weight_kg or "not set",
                "height": member.height_cm or "not provided",
                "age": member.age or "not provided",
                "gender": member.gender.value if member.gender else "not provided",
                "streak": member.streak_days,
                "dietary_preference": member.dietary_preference.value if member.dietary_preference else "not set",
                "onboarding_completed": member.onboarding_completed,
                "has_workout_plan": member_context.get("has_workout_plan", False),
                "has_diet_plan": member_context.get("has_diet_plan", False),
                "progress_summary": progress_text,
                "conversation_history": member_context.get("conversation_history", "First conversation")
            }
        )
        return response
