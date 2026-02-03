"""
Workout Service - Workout plan management and generation
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.workout import WorkoutPlan, WeeklyCheckin
from app.models.member import Member
from app.services.ai_service import ai_service

logger = logging.getLogger(__name__)


class WorkoutService:
    """
    Service for workout plan generation and management.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    async def generate_plan(
        self,
        member: Member,
        week_number: int = 1,
        adaptation_reason: str = None
    ) -> WorkoutPlan:
        """
        Generate a new workout plan for a member.
        Uses AI to create personalized plan based on member profile.
        """
        # Deactivate any existing current plans
        self.db.query(WorkoutPlan).filter(
            and_(
                WorkoutPlan.member_id == member.id,
                WorkoutPlan.is_current == True
            )
        ).update({"is_current": False})
        
        # Determine parameters based on goal
        goal = member.primary_goal.value if member.primary_goal else "general_fitness"
        experience = member.experience_level or "beginner"
        
        # Days per week based on experience
        days_per_week = {
            "beginner": 4,
            "intermediate": 5,
            "advanced": 6
        }.get(experience, 5)
        
        # Generate plan using AI
        plan_json = await ai_service.generate_workout_plan(
            goal=goal,
            experience_level=experience,
            days_per_week=days_per_week,
            duration_mins=45,
            current_weight=member.current_weight_kg,
            target_weight=member.target_weight_kg
        )
        
        # Create workout plan
        workout_plan = WorkoutPlan(
            member_id=member.id,
            week_number=week_number,
            plan_json=plan_json,
            is_current=True,
            adaptation_reason=adaptation_reason,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        
        self.db.add(workout_plan)
        self.db.commit()
        self.db.refresh(workout_plan)
        
        logger.info(f"Generated workout plan for {member.phone} - Week {week_number}")
        return workout_plan
    
    def get_current_plan(self, member_id: UUID) -> Optional[WorkoutPlan]:
        """Get the current active workout plan for a member."""
        return self.db.query(WorkoutPlan).filter(
            and_(
                WorkoutPlan.member_id == member_id,
                WorkoutPlan.is_current == True
            )
        ).first()
    
    def get_plan_history(self, member_id: UUID, limit: int = 10) -> List[WorkoutPlan]:
        """Get workout plan history for a member."""
        return self.db.query(WorkoutPlan).filter(
            WorkoutPlan.member_id == member_id
        ).order_by(WorkoutPlan.week_number.desc()).limit(limit).all()

    def get_plan_summary(self, plan: WorkoutPlan) -> Dict[str, Any]:
        """Get a summary of the workout plan."""
        if not plan:
            return None

        return {
            "focus": plan.plan_json.get("focus", "General Fitness"),
            "days_per_week": plan.plan_json.get("total_days", 4),
            "weekly_tips": plan.plan_json.get("weekly_tips", []),
            "current_week": plan.week_number
        }
    
    def get_todays_workout(self, member: Member) -> Optional[Dict[str, Any]]:
        """Get today's specific workout from current plan."""
        plan = self.get_current_plan(member.id)
        if not plan or not plan.plan_json:
            return None
        
        # Get day of week
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        today = days[datetime.now().weekday()]
        
        days_data = plan.plan_json.get("days", {})
        if today in days_data:
            return {
                "day": today.capitalize(),
                **days_data[today]
            }
        
        return None
    
    def format_workout_for_whatsapp(self, workout: Dict[str, Any]) -> str:
        """Format a workout for WhatsApp message."""
        if not workout:
            return "No workout scheduled for today! 🎉 Rest up!"
        
        lines = [
            f"💪 *{workout.get('day', 'Today')}'s Workout*",
            f"📋 *{workout.get('type', 'Training')}*",
            f"⏱️ {workout.get('duration_mins', 45)} minutes | {workout.get('intensity', 'medium').title()} intensity",
            ""
        ]
        
        # Warmup
        warmup = workout.get("warmup", [])
        if warmup:
            lines.append("🔥 *Warm-up:*")
            for item in warmup:
                lines.append(f"  • {item}")
            lines.append("")
        
        # Exercises
        exercises = workout.get("exercises", [])
        if exercises:
            lines.append("🏋️ *Exercises:*")
            for i, ex in enumerate(exercises, 1):
                if ex.get("id") == "rest":
                    lines.append(f"\n{ex.get('name', 'Rest Day')}")
                    lines.append(f"  {ex.get('reps', 'Take it easy!')}")
                else:
                    lines.append(f"\n{i}. *{ex.get('name', 'Exercise')}*")
                    lines.append(f"   Sets: {ex.get('sets', 3)} | Reps: {ex.get('reps', '10-12')}")
                    lines.append(f"   Rest: {ex.get('rest_secs', 60)}s")
                    if ex.get("notes"):
                        lines.append(f"   💡 {ex['notes']}")
        
        # Cooldown
        cooldown = workout.get("cooldown", [])
        if cooldown:
            lines.append("\n❄️ *Cool-down:*")
            for item in cooldown:
                lines.append(f"  • {item}")
        
        lines.append("\n\nReply with ✅ when done!")
        
        return "\n".join(lines)
    
    def record_checkin(
        self,
        member: Member,
        weight_kg: float = None,
        energy_level: int = None,
        diet_compliance: str = None,
        workouts_completed: int = None
    ) -> WeeklyCheckin:
        """
        Record a weekly check-in for a member.
        """
        # Determine week number
        days_since_start = (datetime.now().date() - member.membership_start).days if member.membership_start else 0
        week_number = (days_since_start // 7) + 1
        
        # Get current plan for planned workouts
        current_plan = self.get_current_plan(member.id)
        workouts_planned = current_plan.plan_json.get("total_days", 5) if current_plan else 5
        
        checkin = WeeklyCheckin(
            member_id=member.id,
            week_start=datetime.now() - timedelta(days=datetime.now().weekday()),
            week_number=week_number,
            weight_kg=weight_kg,
            energy_level=energy_level,
            diet_compliance=diet_compliance,
            workouts_planned=workouts_planned,
            workouts_completed=workouts_completed or 0
        )
        
        self.db.add(checkin)
        
        # Update member's current weight
        if weight_kg:
            member.current_weight_kg = weight_kg
            member.last_checkin_date = datetime.now().date()
        
        self.db.commit()
        self.db.refresh(checkin)
        
        logger.info(f"Recorded check-in for {member.phone} - Week {week_number}")
        return checkin
    
    def get_progress_summary(self, member: Member) -> Dict[str, Any]:
        """
        Get a progress summary for a member.
        """
        checkins = self.db.query(WeeklyCheckin).filter(
            WeeklyCheckin.member_id == member.id
        ).order_by(WeeklyCheckin.week_number.desc()).limit(4).all()
        
        if not checkins:
            return {
                "total_weeks": 0,
                "current_streak": member.streak_days,
                "longest_streak": member.longest_streak,
                "weight_change": 0,
                "message": "Start your journey! Complete your first week to see progress."
            }
        
        # Calculate weight change
        latest_weight = checkins[0].weight_kg if checkins else member.current_weight_kg
        first_weight = checkins[-1].weight_kg if checkins else latest_weight
        weight_change = round(latest_weight - first_weight, 1) if latest_weight and first_weight else 0
        
        # Calculate avg completion rate
        total_completed = sum(c.workouts_completed or 0 for c in checkins)
        total_planned = sum(c.workouts_planned or 5 for c in checkins)
        completion_rate = round((total_completed / total_planned) * 100) if total_planned > 0 else 0
        
        # Determine trend
        goal = member.primary_goal.value if member.primary_goal else "general_fitness"
        if goal == "weight_loss":
            trend = "positive" if weight_change < 0 else "needs_attention"
        elif goal == "muscle_gain":
            trend = "positive" if weight_change > 0 else "needs_attention"
        else:
            trend = "positive" if completion_rate >= 70 else "needs_attention"
        
        return {
            "total_weeks": len(checkins),
            "current_streak": member.streak_days,
            "longest_streak": member.longest_streak,
            "weight_change": weight_change,
            "completion_rate": completion_rate,
            "latest_weight": latest_weight,
            "trend": trend,
            "energy_avg": round(sum(c.energy_level or 3 for c in checkins) / len(checkins), 1)
        }
    
    def format_progress_for_whatsapp(self, member: Member, summary: Dict) -> str:
        """Format progress summary for WhatsApp."""
        goal = member.primary_goal.value if member.primary_goal else "fitness"
        
        # Determine emoji based on weight change and goal
        if goal == "weight_loss":
            weight_emoji = "📉" if summary["weight_change"] < 0 else "📈"
            weight_text = f"{abs(summary['weight_change'])} kg lost" if summary["weight_change"] < 0 else f"{summary['weight_change']} kg"
        elif goal == "muscle_gain":
            weight_emoji = "📈" if summary["weight_change"] > 0 else "📉"
            weight_text = f"+{summary['weight_change']} kg gained" if summary["weight_change"] > 0 else f"{summary['weight_change']} kg"
        else:
            weight_emoji = "⚖️"
            weight_text = f"{summary.get('latest_weight', 'N/A')} kg"
        
        lines = [
            f"📊 *Your Progress Report*",
            f"Week {summary['total_weeks']} of your fitness journey!",
            "",
            f"{weight_emoji} *Weight:* {weight_text}",
            f"🔥 *Streak:* {summary['current_streak']} days",
            f"🏆 *Best Streak:* {summary['longest_streak']} days",
            f"✅ *Workout Completion:* {summary['completion_rate']}%",
            f"⚡ *Avg Energy:* {summary['energy_avg']}/5",
            ""
        ]
        
        # Add motivation
        if summary["trend"] == "positive":
            lines.append("🌟 *Incredible progress!* Keep pushing! 💪")
        else:
            lines.append("💪 *Keep going!* Small steps lead to big changes!")
        
        return "\n".join(lines)
