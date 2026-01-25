"""
Diet Service - Diet plan generation and management
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.diet import DietPlan, WeightLog
from app.models.member import Member
from app.services.ai_service import ai_service

logger = logging.getLogger(__name__)


class DietService:
    """
    Service for diet plan generation and nutrition management.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    async def generate_plan(
        self,
        member: Member,
        week_number: int = 1,
        adaptation_reason: str = None
    ) -> DietPlan:
        """
        Generate a new diet plan for a member.
        Uses AI to create personalized meal plan based on member profile.
        """
        # Deactivate existing current plans
        self.db.query(DietPlan).filter(
            and_(
                DietPlan.member_id == member.id,
                DietPlan.is_current == True
            )
        ).update({"is_current": False})
        
        # Get member details
        goal = member.primary_goal.value if member.primary_goal else "general_fitness"
        diet_pref = member.dietary_preference.value if member.dietary_preference else "non_veg"
        
        # Generate plan using AI
        plan_data = await ai_service.generate_diet_plan(
            goal=goal,
            dietary_preference=diet_pref,
            current_weight=member.current_weight_kg or 70,
            target_weight=member.target_weight_kg or member.current_weight_kg or 70,
            height_cm=member.height_cm or 170,
            age=member.age or 30,
            gender=member.gender.value if member.gender else "male",
            activity_level="moderate"
        )
        
        # Create diet plan
        diet_plan = DietPlan(
            member_id=member.id,
            week_number=week_number,
            daily_calories=plan_data.get("daily_calories", 1800),
            protein_grams=plan_data.get("protein_grams", 100),
            carbs_grams=plan_data.get("carbs_grams", 180),
            fat_grams=plan_data.get("fat_grams", 60),
            plan_json=plan_data,
            is_current=True,
            adaptation_reason=adaptation_reason,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        
        self.db.add(diet_plan)
        self.db.commit()
        self.db.refresh(diet_plan)
        
        logger.info(f"Generated diet plan for {member.phone} - {plan_data.get('daily_calories')} kcal")
        return diet_plan
    
    def get_current_plan(self, member_id: UUID) -> Optional[DietPlan]:
        """Get the current active diet plan for a member."""
        return self.db.query(DietPlan).filter(
            and_(
                DietPlan.member_id == member_id,
                DietPlan.is_current == True
            )
        ).first()
    
    def get_plan_summary(self, plan: DietPlan) -> Dict[str, Any]:
        """Get a summary of the diet plan."""
        if not plan:
            return None
        
        return {
            "daily_calories": plan.daily_calories,
            "protein": plan.protein_grams,
            "carbs": plan.carbs_grams,
            "fat": plan.fat_grams,
            "macro_ratio": plan.macro_ratio,
            "meals": list(plan.plan_json.get("meals", {}).keys()),
            "tips": plan.plan_json.get("tips", [])
        }
    
    def format_plan_for_whatsapp(self, plan: DietPlan) -> str:
        """Format full diet plan for WhatsApp message (shortened version)."""
        if not plan:
            return "No diet plan generated yet. Let me create one for you!"
        
        lines = [
            "🍎 *Your Personalized Diet Plan*",
            "",
            f"📊 *Daily Targets:*",
            f"  🔥 Calories: {plan.daily_calories} kcal",
            f"  💪 Protein: {plan.protein_grams}g",
            f"  🌾 Carbs: {plan.carbs_grams}g",
            f"  🥑 Fat: {plan.fat_grams}g",
            ""
        ]
        
        meals = plan.plan_json.get("meals", {})
        lines.append("📋 *Today's Meals:*")
        
        for meal_key, meal in meals.items():
            meal_name = meal_key.replace("_", " ").title()
            lines.append(f"\n*{meal.get('time', '')} - {meal.get('name', meal_name)}*")
            for item in meal.get("items", [])[:3]:  # Show max 3 items
                lines.append(f"  • {item}")
            if len(meal.get("items", [])) > 3:
                lines.append(f"  ... +{len(meal['items']) - 3} more")
        
        # Add tips
        tips = plan.plan_json.get("tips", [])
        if tips:
            lines.append("\n💡 *Tips:*")
            for tip in tips[:2]:
                lines.append(f"  • {tip}")
        
        lines.append(f"\n💧 *Hydration:* {plan.plan_json.get('hydration', '3-4L water')}")
        
        return "\n".join(lines)
    
    def format_single_meal(self, plan: DietPlan, meal_type: str) -> str:
        """Format a single meal for quick reference."""
        if not plan:
            return "No diet plan found."
        
        meals = plan.plan_json.get("meals", {})
        meal = meals.get(meal_type)
        
        if not meal:
            return f"No {meal_type.replace('_', ' ')} found in your plan."
        
        lines = [
            f"🍽️ *{meal.get('name', meal_type.replace('_', ' ').title())}*",
            f"⏰ {meal.get('time', '')}",
            ""
        ]
        
        for item in meal.get("items", []):
            lines.append(f"• {item}")
        
        lines.append(f"\n📊 ~{meal.get('calories', 0)} kcal | {meal.get('protein', 0)}g protein")
        
        # Alternatives
        alts = meal.get("alternatives", [])
        if alts:
            lines.append(f"\n🔄 *Alternatives:* {alts[0]}")
        
        return "\n".join(lines)
    
    def log_weight(
        self,
        member: Member,
        weight_kg: float,
        notes: str = None
    ) -> WeightLog:
        """
        Log member's weight.
        """
        log = WeightLog(
            member_id=member.id,
            weight_kg=weight_kg,
            notes=notes,
            time_of_day="morning" if datetime.now().hour < 12 else "evening"
        )
        
        self.db.add(log)
        
        # Update member's current weight
        member.current_weight_kg = weight_kg
        
        self.db.commit()
        self.db.refresh(log)
        
        logger.info(f"Logged weight for {member.phone}: {weight_kg} kg")
        return log
    
    def get_weight_history(self, member_id: UUID, days: int = 30) -> List[WeightLog]:
        """Get weight history for a member."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        return self.db.query(WeightLog).filter(
            and_(
                WeightLog.member_id == member_id,
                WeightLog.logged_at >= cutoff
            )
        ).order_by(WeightLog.logged_at.desc()).all()
    
    def get_weight_trend(self, member: Member, weeks: int = 4) -> Dict[str, Any]:
        """
        Analyze weight trend over time.
        """
        history = self.get_weight_history(member.id, days=weeks * 7)
        
        if len(history) < 2:
            return {
                "trend": "insufficient_data",
                "change": 0,
                "weekly_avg_change": 0,
                "message": "Need more data to analyze trend"
            }
        
        # Calculate change
        latest = history[0].weight_kg
        oldest = history[-1].weight_kg
        total_change = round(latest - oldest, 2)
        weeks_tracked = max(1, (history[0].logged_at - history[-1].logged_at).days / 7)
        weekly_avg = round(total_change / weeks_tracked, 2)
        
        # Determine trend based on goal
        goal = member.primary_goal.value if member.primary_goal else "general_fitness"
        
        if goal == "weight_loss":
            if weekly_avg < -0.5:
                trend = "good"
                message = "Great progress! You're losing weight at a healthy rate."
            elif weekly_avg < 0:
                trend = "slow"
                message = "Making progress! Consider increasing activity slightly."
            else:
                trend = "plateau"
                message = "Weight plateau detected. Let's adjust your plan."
        elif goal == "muscle_gain":
            if weekly_avg > 0.2 and weekly_avg < 0.5:
                trend = "good"
                message = "Perfect lean gain rate! Keep it up."
            elif weekly_avg >= 0.5:
                trend = "fast"
                message = "Gaining quickly - watch fat gain. Consider slight calorie reduction."
            else:
                trend = "slow"
                message = "Not gaining enough. Increase calories and protein."
        else:
            if abs(weekly_avg) < 0.3:
                trend = "stable"
                message = "Weight is stable. Good maintenance!"
            else:
                trend = "fluctuating"
                message = "Some weight fluctuation. Stay consistent with diet."
        
        return {
            "trend": trend,
            "total_change": total_change,
            "weekly_avg_change": weekly_avg,
            "latest_weight": latest,
            "message": message
        }
