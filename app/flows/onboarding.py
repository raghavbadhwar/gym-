"""
Onboarding Flow - New member onboarding via WhatsApp
"""
import logging
from typing import Dict, Any, Optional, Union
from sqlalchemy.orm import Session
from fastapi.concurrency import run_in_threadpool

from app.services.member_service import MemberService
from app.services.workout_service import WorkoutService
from app.services.diet_service import DietService
from app.config import settings

logger = logging.getLogger(__name__)


class OnboardingFlow:
    """
    Handles new member onboarding via WhatsApp.
    Collects: Name confirmation -> Goal -> Dietary preference -> Weight
    Then generates initial workout and diet plans.
    """
    
    FLOW_NAME = "onboarding"
    
    def __init__(self, db: Session):
        self.db = db
        self.member_service = MemberService(db)
        self.workout_service = WorkoutService(db)
        self.diet_service = DietService(db)
    
    async def start(self, member) -> Dict:
        """
        Start onboarding flow for a new member.
        Returns welcome message with goal selection buttons.
        """
        # Set conversation state
        self.member_service.set_conversation_state(
            phone=member.phone,
            flow=self.FLOW_NAME,
            step="goal_selection",
            data={"name": member.name}
        )
        
        return {
            "type": "buttons",
            "header": f"Welcome to {settings.gym_name}! 🎉",
            "body": f"Hi {member.name}! I'm GymBuddy, your AI fitness companion.\n\nI'll create a personalized workout and diet plan just for you. Let's start!\n\n*What's your #1 fitness goal?*",
            "buttons": [
                {"id": "goal_weight_loss", "title": "Lose Weight 🏃"},
                {"id": "goal_muscle_gain", "title": "Build Muscle 💪"},
                {"id": "goal_fitness", "title": "Stay Fit 🌟"}
            ],
            "footer": "GymBuddy - Your AI Fitness Coach"
        }
    
    async def resume(self, member, message: Dict) -> Optional[Union[str, Dict]]:
        """Resume incomplete onboarding."""
        step = member.onboarding_step or "goal_selection"
        
        # Get or create conversation state
        conv_state = self.member_service.get_conversation_state(member.phone)
        if not conv_state:
            self.member_service.set_conversation_state(
                member.phone, self.FLOW_NAME, step, {"name": member.name}
            )
            conv_state = self.member_service.get_conversation_state(member.phone)
        
        return await self.handle_step(conv_state, member, message)
    
    async def handle_step(
        self,
        conv_state,
        member,
        message: Dict
    ) -> Optional[Union[str, Dict]]:
        """
        Handle a step in the onboarding flow.
        """
        step = conv_state.current_step
        content = message.get("content", "").strip().lower()
        flow_data = conv_state.flow_data or {}
        
        logger.info(f"Onboarding step: {step}, content: {content}")
        
        if step == "goal_selection":
            return await self._handle_goal_selection(member, content, flow_data)
        
        elif step == "dietary_preference":
            return await self._handle_dietary_preference(member, content, flow_data)
        
        elif step == "weight":
            return await self._handle_weight(member, content, flow_data)
        
        elif step == "height":
            return await self._handle_height(member, content, flow_data)
        
        elif step == "age":
            return await self._handle_age(member, content, flow_data)
        
        else:
            # Unknown step, restart
            return await self.start(member)
    
    async def _handle_goal_selection(
        self,
        member,
        content: str,
        flow_data: dict
    ) -> Dict:
        """Handle goal selection."""
        # Parse goal from button or text
        goal = None
        if "goal_weight_loss" in content or "weight" in content or "lose" in content or "fat" in content:
            goal = "weight_loss"
        elif "goal_muscle" in content or "muscle" in content or "build" in content or "gain" in content:
            goal = "muscle_gain"
        elif "goal_fitness" in content or "fit" in content or "health" in content:
            goal = "general_fitness"
        
        if not goal:
            return {
                "type": "buttons",
                "body": "Please select your fitness goal:",
                "buttons": [
                    {"id": "goal_weight_loss", "title": "Lose Weight 🏃"},
                    {"id": "goal_muscle_gain", "title": "Build Muscle 💪"},
                    {"id": "goal_fitness", "title": "Stay Fit 🌟"}
                ]
            }
        
        flow_data["goal"] = goal
        
        # Update member and state
        member.onboarding_step = "dietary_preference"
        self.db.commit()
        
        self.member_service.set_conversation_state(
            member.phone, self.FLOW_NAME, "dietary_preference", flow_data
        )
        
        goal_msg = {
            "weight_loss": "weight loss",
            "muscle_gain": "muscle building", 
            "general_fitness": "staying fit"
        }.get(goal, goal)
        
        return {
            "type": "buttons",
            "body": f"Great choice! I'll design a plan focused on *{goal_msg}*.\n\n*What's your dietary preference?*",
            "buttons": [
                {"id": "diet_veg", "title": "Vegetarian 🥬"},
                {"id": "diet_nonveg", "title": "Non-Veg 🍗"},
                {"id": "diet_egg", "title": "Eggetarian 🥚"}
            ]
        }
    
    async def _handle_dietary_preference(
        self,
        member,
        content: str,
        flow_data: dict
    ) -> str:
        """Handle dietary preference selection."""
        diet_pref = None
        if "diet_veg" in content or (content == "veg" or "vegetarian" in content):
            diet_pref = "veg"
        elif "diet_nonveg" in content or "non" in content or "chicken" in content or "meat" in content:
            diet_pref = "non_veg"
        elif "diet_egg" in content or "egg" in content:
            diet_pref = "eggetarian"
        
        if not diet_pref:
            return {
                "type": "buttons",
                "body": "Please select your dietary preference:",
                "buttons": [
                    {"id": "diet_veg", "title": "Vegetarian 🥬"},
                    {"id": "diet_nonveg", "title": "Non-Veg 🍗"},
                    {"id": "diet_egg", "title": "Eggetarian 🥚"}
                ]
            }
        
        flow_data["diet_pref"] = diet_pref
        
        # Update state
        member.onboarding_step = "weight"
        self.db.commit()
        
        self.member_service.set_conversation_state(
            member.phone, self.FLOW_NAME, "weight", flow_data
        )
        
        diet_msg = {
            "veg": "vegetarian",
            "non_veg": "non-vegetarian",
            "eggetarian": "eggetarian"
        }.get(diet_pref, diet_pref)
        
        return f"""Perfect! I'll create {diet_msg} meal plans for you. 🍎

*What's your current weight?*
(Just type a number, e.g., 72 or 72.5)"""
    
    async def _handle_weight(
        self,
        member,
        content: str,
        flow_data: dict
    ) -> str:
        """Handle weight input."""
        try:
            # Clean input
            weight_str = content.replace("kg", "").replace("kgs", "").strip()
            weight = float(weight_str)
            
            if weight < 30 or weight > 250:
                return "That doesn't seem right. Please enter your weight in kg (e.g., 72)"
            
            flow_data["weight"] = weight
            
            # Update state
            member.onboarding_step = "height"
            self.db.commit()
            
            self.member_service.set_conversation_state(
                member.phone, self.FLOW_NAME, "height", flow_data
            )
            
            return f"""Got it! {weight} kg recorded. 📝

*What's your height?*
(Type in cm, e.g., 170)"""
            
        except ValueError:
            return "Please enter your weight as a number (e.g., 72 or 72.5)"
    
    async def _handle_height(
        self,
        member,
        content: str,
        flow_data: dict
    ) -> str:
        """Handle height input."""
        try:
            # Clean input
            height_str = content.replace("cm", "").replace("'", "").replace('"', '').strip()
            
            # Handle feet.inches format
            if "." in height_str and float(height_str) < 10:
                parts = height_str.split(".")
                feet = int(parts[0])
                inches = int(parts[1]) if len(parts) > 1 else 0
                height = int((feet * 30.48) + (inches * 2.54))
            else:
                height = int(float(height_str))
            
            if height < 100 or height > 250:
                return "Please enter your height in cm (e.g., 170)"
            
            flow_data["height"] = height
            
            # Update state
            member.onboarding_step = "age"
            self.db.commit()
            
            self.member_service.set_conversation_state(
                member.phone, self.FLOW_NAME, "age", flow_data
            )
            
            return f"""Perfect! {height} cm. 📏

*Last question - What's your age?*"""
            
        except ValueError:
            return "Please enter your height in cm (e.g., 170)"
    
    async def _handle_age(
        self,
        member,
        content: str,
        flow_data: dict
    ) -> str:
        """Handle age input and complete onboarding."""
        try:
            age = int(content.replace("years", "").replace("yrs", "").strip())
            
            if age < 14 or age > 100:
                return "Please enter a valid age (14-100)"
            
            flow_data["age"] = age
            
            # Complete onboarding
            self.member_service.complete_onboarding(
                member,
                goal=flow_data.get("goal"),
                dietary_pref=flow_data.get("diet_pref"),
                weight=flow_data.get("weight"),
                height=flow_data.get("height"),
                age=age
            )
            
            # Generate initial plans
            await self._generate_initial_plans(member)
            
            # Clear conversation state
            self.member_service.clear_conversation_state(member.phone)
            
            goal_text = {
                "weight_loss": "to help you lose weight",
                "muscle_gain": "to build muscle",
                "general_fitness": "to keep you fit and healthy"
            }.get(flow_data.get("goal"), "for your fitness journey")
            
            return f"""🎉 *You're all set, {member.name}!*

I've created personalized plans {goal_text}:

✅ Custom workout plan
✅ Personalized diet plan with {flow_data.get('diet_pref', 'your preferred')} options
✅ Progress tracking ready

*Ready to crush it?* 💪

Reply:
💪 *workout* - See today's workout
🍎 *diet* - View your meal plan
📅 *classes* - Book a class
📊 *progress* - Check your stats

Let's get started!"""
            
        except ValueError:
            return "Please enter your age as a number (e.g., 28)"
    
    async def _generate_initial_plans(self, member):
        """Generate initial workout and diet plans for new member."""
        try:
            # Generate workout plan
            await run_in_threadpool(self.workout_service.generate_plan, member, week_number=1)
            logger.info(f"Generated workout plan for {member.phone}")
            
            # Generate diet plan
            await run_in_threadpool(self.diet_service.generate_plan, member, week_number=1)
            logger.info(f"Generated diet plan for {member.phone}")
            
        except Exception as e:
            logger.error(f"Error generating initial plans: {e}")
