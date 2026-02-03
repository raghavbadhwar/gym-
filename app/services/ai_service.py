"""
AI Service - Gemini-powered plan generation and NLU
"""
import json
import logging
from typing import Optional, Dict, Any, List
import google.generativeai as genai
from fastapi.concurrency import run_in_threadpool

from app.config import settings

logger = logging.getLogger(__name__)


class AIService:
    """
    Service for AI-powered features using Google Gemini.
    - Workout plan generation
    - Diet plan generation
    - Intent classification
    - Natural conversation handling
    """
    
    def __init__(self):
        if settings.gemini_api_key:
            genai.configure(api_key=settings.gemini_api_key)
            self.model = genai.GenerativeModel(settings.gemini_model)
        else:
            self.model = None
            logger.warning("Gemini API key not configured. AI features disabled.")
    
    async def generate_workout_plan(
        self,
        goal: str,
        experience_level: str,
        days_per_week: int = 5,
        duration_mins: int = 45,
        available_equipment: List[str] = None,
        restrictions: List[str] = None,
        current_weight: float = None,
        target_weight: float = None
    ) -> Dict[str, Any]:
        """
        Generate a personalized weekly workout plan.
        
        Returns:
            {
                "focus": "Fat Burning & Muscle Toning",
                "total_days": 5,
                "days": {
                    "monday": {
                        "type": "Upper Body",
                        "duration_mins": 45,
                        "intensity": "medium",
                        "exercises": [
                            {
                                "id": "bench_press",
                                "name": "Bench Press",
                                "sets": 3,
                                "reps": "10-12",
                                "rest_secs": 60,
                                "notes": "Focus on form"
                            }
                        ]
                    }
                }
            }
        """
        if not self.model:
            return self._get_default_workout_plan(goal, days_per_week)
        
        equipment = ", ".join(available_equipment) if available_equipment else "full gym equipment"
        restrictions_text = ", ".join(restrictions) if restrictions else "none"
        
        prompt = f"""Generate a detailed {days_per_week}-day weekly workout plan in JSON format.

MEMBER PROFILE:
- Goal: {goal}
- Experience: {experience_level}
- Workout duration: {duration_mins} minutes per session
- Available equipment: {equipment}
- Restrictions/Injuries: {restrictions_text}
- Current weight: {current_weight or 'Not specified'} kg
- Target weight: {target_weight or 'Not specified'} kg

REQUIREMENTS:
1. Plan should be progressive and suitable for {experience_level} level
2. Include warm-up and cool-down suggestions
3. Provide clear exercise instructions
4. Balance muscle groups properly
5. Include rest days appropriately

Return ONLY valid JSON in this exact format:
{{
    "focus": "Brief description of plan focus",
    "total_days": {days_per_week},
    "weekly_tips": ["tip 1", "tip 2"],
    "days": {{
        "monday": {{
            "type": "Workout type (e.g., Upper Body, Cardio, Full Body)",
            "duration_mins": {duration_mins},
            "intensity": "low|medium|high",
            "warmup": ["5 min light cardio", "dynamic stretches"],
            "exercises": [
                {{
                    "id": "exercise_id_lowercase",
                    "name": "Exercise Name",
                    "sets": 3,
                    "reps": "10-12",
                    "rest_secs": 60,
                    "notes": "Form tips or variations"
                }}
            ],
            "cooldown": ["5 min stretching"]
        }},
        "tuesday": {{ ... }},
        ...
    }}
}}

Include exercises appropriate for a gym in India."""

        try:
            response = await self._generate_json(prompt)
            return response
        except Exception as e:
            logger.error(f"Error generating workout plan: {e}")
            return self._get_default_workout_plan(goal, days_per_week)
    
    def generate_diet_plan(
        self,
        goal: str,
        dietary_preference: str,  # veg, non_veg, eggetarian, vegan
        current_weight: float,
        target_weight: float,
        height_cm: int,
        age: int,
        gender: str,
        activity_level: str = "moderate"  # sedentary, light, moderate, active, very_active
    ) -> Dict[str, Any]:
        """
        Generate a personalized diet plan with Indian food options.
        
        Returns:
            {
                "daily_calories": 1800,
                "protein_grams": 120,
                "carbs_grams": 180,
                "fat_grams": 60,
                "meals": { ... }
            }
        """
        if not self.model:
            return self._get_default_diet_plan(goal, dietary_preference)
        
        # Calculate BMR using Mifflin-St Jeor
        if gender.lower() == "male":
            bmr = 10 * current_weight + 6.25 * height_cm - 5 * age + 5
        else:
            bmr = 10 * current_weight + 6.25 * height_cm - 5 * age - 161
        
        # Activity multipliers
        activity_multipliers = {
            "sedentary": 1.2,
            "light": 1.375,
            "moderate": 1.55,
            "active": 1.725,
            "very_active": 1.9
        }
        
        tdee = bmr * activity_multipliers.get(activity_level, 1.55)
        
        # Adjust for goal
        if goal == "weight_loss":
            target_calories = int(tdee - 500)  # 500 cal deficit
        elif goal == "muscle_gain":
            target_calories = int(tdee + 300)  # 300 cal surplus
        else:
            target_calories = int(tdee)
        
        prompt = f"""Generate a detailed daily meal plan in JSON format.

MEMBER PROFILE:
- Goal: {goal}
- Dietary preference: {dietary_preference.upper()}
- Current weight: {current_weight} kg
- Target weight: {target_weight} kg
- Age: {age}, Gender: {gender}
- Activity level: {activity_level}
- Estimated TDEE: {int(tdee)} calories
- Target calories: {target_calories} calories

REQUIREMENTS:
1. All meals must be {dietary_preference.upper()} friendly
2. Use INDIAN FOOD OPTIONS primarily (dal, roti, rice, sabzi, etc.)
3. Include pre and post workout nutrition
4. Practical and easy to follow
5. Include hydration recommendations
6. Suggest affordable, locally available foods

Return ONLY valid JSON in this exact format:
{{
    "daily_calories": {target_calories},
    "protein_grams": (calculate based on goal, typically 1.6-2.2g per kg for muscle gain),
    "carbs_grams": (remaining calories from carbs),
    "fat_grams": (about 25-30% of calories),
    "meals": {{
        "early_morning": {{
            "time": "6:00 AM",
            "name": "Meal name",
            "items": ["item 1 with quantity", "item 2"],
            "calories": 100,
            "protein": 5,
            "alternatives": ["alternative option 1"]
        }},
        "breakfast": {{ ... }},
        "mid_morning": {{ ... }},
        "lunch": {{ ... }},
        "evening_snack": {{ ... }},
        "dinner": {{ ... }},
        "pre_workout": {{ ... }},
        "post_workout": {{ ... }}
    }},
    "hydration": "3-4 liters of water daily",
    "supplements": [
        {{"name": "Supplement name", "timing": "when to take", "optional": true}}
    ],
    "tips": ["Tip 1", "Tip 2", "Tip 3"]
}}"""

        try:
            response = self._generate_json_sync(prompt)
            return response
        except Exception as e:
            logger.error(f"Error generating diet plan: {e}")
            return self._get_default_diet_plan(goal, dietary_preference)
    
    async def classify_intent(self, message: str) -> Dict[str, Any]:
        """
        Classify user intent from a message.
        
        Returns:
            {
                "intent": "book_class|check_progress|get_workout|...",
                "confidence": 0.95,
                "entities": {"class_type": "yoga", "time": "6am"}
            }
        """
        if not self.model:
            return self._simple_intent_classification(message)
        
        prompt = f"""Classify the user's intent from this gym-related message.

MESSAGE: "{message}"

POSSIBLE INTENTS:
- greet: Hello, hi, hey, good morning, etc.
- book_class: Want to book a class
- cancel_booking: Cancel a class booking
- check_schedule: View class schedule
- get_workout: Ask for today's workout or workout plan
- get_diet: Ask about diet or meal plan
- log_workout: Report completing a workout
- check_progress: Ask about progress, weight, stats
- check_streak: Ask about workout streak
- renew_membership: Renew or extend membership
- talk_trainer: Want to speak to a trainer
- help: Need help or don't understand
- other: Anything else

Return ONLY valid JSON:
{{
    "intent": "intent_name",
    "confidence": 0.0 to 1.0,
    "entities": {{
        "class_type": "if mentioned (yoga, hiit, spin, etc.)",
        "time": "if mentioned",
        "date": "if mentioned",
        "other_entity": "value"
    }}
}}"""

        try:
            response = await self._generate_json(prompt)
            return response
        except Exception as e:
            logger.error(f"Error classifying intent: {e}")
            return self._simple_intent_classification(message)
    
    async def adapt_plan(
        self,
        current_plan: Dict,
        progress_data: Dict,
        goal: str
    ) -> Dict[str, Any]:
        """
        Suggest adaptations to a workout/diet plan based on progress.
        
        Args:
            current_plan: Current workout or diet plan
            progress_data: {weight_trend, energy_level, adherence_rate, etc.}
            goal: weight_loss, muscle_gain, etc.
        
        Returns:
            {
                "should_adapt": True,
                "adaptations": ["Increase protein by 20g", "Add rest day"],
                "new_plan": { ... }
            }
        """
        if not self.model:
            return {"should_adapt": False, "adaptations": [], "new_plan": current_plan}
        
        prompt = f"""Analyze this fitness progress and suggest plan adaptations.

CURRENT PLAN:
{json.dumps(current_plan, indent=2)}

PROGRESS DATA:
{json.dumps(progress_data, indent=2)}

GOAL: {goal}

ADAPTATION RULES:
- If weight loss stalled for 2+ weeks: reduce calories by 100, change workout variety
- If energy consistently low (<3/5): add rest day, check nutrition
- If losing weight too fast (>1.5kg/week): increase calories
- If not completing workouts: reduce intensity or frequency
- If plateau in muscle gain: increase protein, change exercises

Return ONLY valid JSON:
{{
    "should_adapt": true/false,
    "reason": "Why adaptation is needed or not",
    "adaptations": [
        "Specific change 1",
        "Specific change 2"
    ],
    "motivation_message": "Encouraging message for the member"
}}"""

        try:
            response = await self._generate_json(prompt)
            return response
        except Exception as e:
            logger.error(f"Error adapting plan: {e}")
            return {"should_adapt": False, "adaptations": [], "new_plan": current_plan}
    
    async def _generate_json(self, prompt: str) -> Dict:
        """Generate JSON response from Gemini (Async wrapper)."""
        return await run_in_threadpool(self._generate_json_sync, prompt)

    def _generate_json_sync(self, prompt: str) -> Dict:
        """Generate JSON response from Gemini (Synchronous)."""
        response = self.model.generate_content(prompt)
        text = response.text.strip()
        
        # Clean up response - remove markdown code blocks if present
        if text.startswith("```"):
            text = text.split("\n", 1)[1]  # Remove first line
        if text.endswith("```"):
            text = text.rsplit("\n", 1)[0]  # Remove last line
        if text.startswith("json"):
            text = text[4:].strip()
        
        return json.loads(text)
    
    def _simple_intent_classification(self, message: str) -> Dict[str, Any]:
        """Fallback intent classification without AI."""
        message = message.lower().strip()
        
        intents = {
            "greet": ["hi", "hello", "hey", "good morning", "good evening", "namaste"],
            "book_class": ["book", "class", "schedule class", "join class", "slot"],
            "cancel_booking": ["cancel", "unbook", "remove booking"],
            "check_schedule": ["schedule", "classes today", "what classes", "timing"],
            "get_workout": ["workout", "exercise", "today's workout", "routine"],
            "get_diet": ["diet", "meal", "food", "nutrition", "eat", "calories"],
            "log_workout": ["done", "completed", "finished workout"],
            "check_progress": ["progress", "weight", "stats", "how am i doing"],
            "check_streak": ["streak", "how many days"],
            "help": ["help", "?", "confused", "don't understand"]
        }
        
        for intent, keywords in intents.items():
            for keyword in keywords:
                if keyword in message:
                    return {"intent": intent, "confidence": 0.7, "entities": {}}
        
        return {"intent": "other", "confidence": 0.5, "entities": {}}
    
    def _get_default_workout_plan(self, goal: str, days: int = 5) -> Dict:
        """Return a default workout plan when AI is unavailable."""
        return {
            "focus": "Full Body Fitness",
            "total_days": days,
            "weekly_tips": ["Stay hydrated", "Rest well between sets", "Focus on form over weight"],
            "days": {
                "monday": {
                    "type": "Upper Body",
                    "duration_mins": 45,
                    "intensity": "medium",
                    "warmup": ["5 min treadmill", "Arm circles"],
                    "exercises": [
                        {"id": "bench_press", "name": "Bench Press", "sets": 3, "reps": "10-12", "rest_secs": 60, "notes": "Control movement"},
                        {"id": "shoulder_press", "name": "Shoulder Press", "sets": 3, "reps": "10-12", "rest_secs": 60, "notes": "Keep core tight"},
                        {"id": "lat_pulldown", "name": "Lat Pulldown", "sets": 3, "reps": "12", "rest_secs": 60, "notes": "Full stretch"},
                        {"id": "bicep_curls", "name": "Bicep Curls", "sets": 3, "reps": "12", "rest_secs": 45, "notes": "No swinging"},
                        {"id": "tricep_pushdown", "name": "Tricep Pushdown", "sets": 3, "reps": "12", "rest_secs": 45, "notes": "Squeeze at bottom"}
                    ],
                    "cooldown": ["Stretching 5 mins"]
                },
                "tuesday": {
                    "type": "Lower Body",
                    "duration_mins": 45,
                    "intensity": "medium",
                    "warmup": ["5 min cycling", "Leg swings"],
                    "exercises": [
                        {"id": "squats", "name": "Squats", "sets": 4, "reps": "10-12", "rest_secs": 90, "notes": "Depth below parallel"},
                        {"id": "leg_press", "name": "Leg Press", "sets": 3, "reps": "12", "rest_secs": 60, "notes": "Full range"},
                        {"id": "lunges", "name": "Walking Lunges", "sets": 3, "reps": "10 each", "rest_secs": 60, "notes": "Keep torso upright"},
                        {"id": "leg_curl", "name": "Leg Curls", "sets": 3, "reps": "12", "rest_secs": 45, "notes": "Controlled"},
                        {"id": "calf_raises", "name": "Calf Raises", "sets": 4, "reps": "15", "rest_secs": 30, "notes": "Full stretch"}
                    ],
                    "cooldown": ["Foam rolling", "Stretching 5 mins"]
                },
                "wednesday": {
                    "type": "Rest Day",
                    "duration_mins": 0,
                    "intensity": "low",
                    "warmup": [],
                    "exercises": [{"id": "rest", "name": "Active Recovery", "sets": 1, "reps": "Optional light walk or yoga", "rest_secs": 0, "notes": "Take it easy!"}],
                    "cooldown": []
                },
                "thursday": {
                    "type": "Push Day",
                    "duration_mins": 45,
                    "intensity": "medium",
                    "warmup": ["5 min cardio", "Shoulder rotations"],
                    "exercises": [
                        {"id": "incline_press", "name": "Incline Dumbbell Press", "sets": 3, "reps": "10-12", "rest_secs": 60, "notes": "30-degree incline"},
                        {"id": "dips", "name": "Dips", "sets": 3, "reps": "8-10", "rest_secs": 60, "notes": "Use assist if needed"},
                        {"id": "lateral_raises", "name": "Lateral Raises", "sets": 3, "reps": "12-15", "rest_secs": 45, "notes": "Light weight, control"},
                        {"id": "cable_fly", "name": "Cable Fly", "sets": 3, "reps": "12", "rest_secs": 45, "notes": "Squeeze chest"}
                    ],
                    "cooldown": ["Stretching 5 mins"]
                },
                "friday": {
                    "type": "Pull Day",
                    "duration_mins": 45,
                    "intensity": "medium",
                    "warmup": ["5 min rowing", "Band pull-aparts"],
                    "exercises": [
                        {"id": "deadlift", "name": "Deadlift", "sets": 4, "reps": "6-8", "rest_secs": 120, "notes": "Keep back straight"},
                        {"id": "rows", "name": "Barbell Rows", "sets": 3, "reps": "10-12", "rest_secs": 60, "notes": "Pull to stomach"},
                        {"id": "pullups", "name": "Pull-ups", "sets": 3, "reps": "As many as possible", "rest_secs": 90, "notes": "Use assist if needed"},
                        {"id": "face_pulls", "name": "Face Pulls", "sets": 3, "reps": "15", "rest_secs": 45, "notes": "Squeeze rear delts"}
                    ],
                    "cooldown": ["Stretching 5 mins"]
                }
            }
        }
    
    def _get_default_diet_plan(self, goal: str, diet_pref: str) -> Dict:
        """Return a default diet plan when AI is unavailable."""
        is_veg = diet_pref in ["veg", "vegan"]
        
        base_plan = {
            "daily_calories": 1800 if goal == "weight_loss" else 2200,
            "protein_grams": 100,
            "carbs_grams": 180,
            "fat_grams": 60,
            "meals": {
                "early_morning": {
                    "time": "6:00 AM",
                    "name": "Pre-Workout",
                    "items": ["1 banana", "5 soaked almonds", "1 glass warm water with lemon"],
                    "calories": 150,
                    "protein": 4
                },
                "breakfast": {
                    "time": "8:00 AM",
                    "name": "Power Breakfast",
                    "items": [
                        "2 egg white omelette with veggies" if not is_veg else "Moong dal chilla (2 pcs)",
                        "2 multigrain toast",
                        "1 glass milk"
                    ],
                    "calories": 350,
                    "protein": 20
                },
                "mid_morning": {
                    "time": "11:00 AM",
                    "name": "Protein Snack",
                    "items": ["Greek yogurt with berries" if not is_veg else "Chana chaat (1 cup)", "Green tea"],
                    "calories": 150,
                    "protein": 12
                },
                "lunch": {
                    "time": "1:00 PM",
                    "name": "Balanced Lunch",
                    "items": [
                        "1 cup rice or 2 roti",
                        "1 cup dal",
                        "Grilled chicken (100g)" if not is_veg else "Paneer bhurji (100g)",
                        "Mixed vegetable sabzi",
                        "Salad with cucumber & tomato"
                    ],
                    "calories": 500,
                    "protein": 35
                },
                "evening_snack": {
                    "time": "5:00 PM",
                    "name": "Pre-Workout Snack",
                    "items": ["1 apple or banana", "Handful of peanuts", "Black coffee (optional)"],
                    "calories": 200,
                    "protein": 8
                },
                "dinner": {
                    "time": "8:00 PM",
                    "name": "Light Dinner",
                    "items": [
                        "2 roti or 1 cup brown rice",
                        "Fish curry (150g)" if not is_veg else "Tofu stir fry (150g)",
                        "Vegetable soup",
                        "Small salad"
                    ],
                    "calories": 400,
                    "protein": 30
                },
                "post_workout": {
                    "time": "After workout",
                    "name": "Recovery",
                    "items": ["Protein shake" if not is_veg else "Soy protein shake", "1 banana"],
                    "calories": 200,
                    "protein": 25
                }
            },
            "hydration": "3-4 liters of water daily",
            "supplements": [
                {"name": "Whey Protein" if not is_veg else "Plant Protein", "timing": "Post-workout", "optional": False},
                {"name": "Multivitamin", "timing": "With breakfast", "optional": True}
            ],
            "tips": [
                "Eat protein with every meal",
                "Avoid processed foods and sugar",
                "Don't skip meals",
                "Eat slowly and chew properly",
                "Avoid eating after 9 PM"
            ]
        }
        
        return base_plan


# Singleton instance
ai_service = AIService()
