"""
GymBot-Core Configuration
Loads all settings from environment variables
Production-ready, autonomous WhatsApp Agent backend for Gyms.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional, Literal


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database (SQLite by default - no Docker needed!)
    # Easily swappable to PostgreSQL: postgresql://user:pass@localhost:5432/gymbot
    database_url: str = "sqlite:///./gymbuddy.db"
    redis_url: str = ""  # Optional - leave empty to skip Redis
    
    # WhatsApp Business API
    whatsapp_phone_number_id: str = ""
    whatsapp_business_account_id: str = ""
    whatsapp_access_token: str = ""
    whatsapp_verify_token: str = "gymbuddy_verify_token_2026"
    whatsapp_app_secret: str = ""
    whatsapp_api_url: str = "https://graph.facebook.com/v18.0"
    
    # AI Configuration - Choose your provider
    ai_provider: Literal["openai", "gemini"] = "openai"  # openai or gemini
    
    # OpenAI API
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"  # Default to GPT-4o-mini as specified
    
    # Gemini AI (alternative)
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"  # Updated to latest model
    
    # App Settings
    app_env: str = "development"
    app_secret_key: str = "change-this-secret-key-in-production"
    gym_name: str = "FitZone Gym"
    gym_phone: str = "+919876543210"
    
    # Escalation Settings (for HUMAN_HELP intent)
    manager_phone: str = ""  # Manager's WhatsApp for escalation
    escalation_email: str = ""  # Email for escalation notifications
    
    # Webhook
    webhook_url: Optional[str] = None
    
    # System Prompt for AI persona - Gym Specialized
    @property
    def system_prompt(self) -> str:
        return f"""You are GymBuddy, the AI fitness assistant for {self.gym_name} - an Indian gym helping members achieve their fitness goals.

## YOUR IDENTITY
- Name: GymBuddy
- Role: Personal AI fitness coach and gym assistant
- Personality: Energetic, motivating, knowledgeable, friendly but professional
- Language: Mix English with casual Hindi phrases (bhai, yaar, chal, etc.) to sound natural

## YOUR CAPABILITIES
1. **Workout Plans**: Create personalized workout routines based on member's goal, experience, and equipment
2. **Diet Plans**: Provide Indian cuisine-friendly meal plans (dal, roti, rice, paneer, etc.)
3. **Class Booking**: Help book yoga, HIIT, spin, strength classes with timing and trainer info
4. **Progress Tracking**: Track weight, streaks, workouts completed, achievements
5. **Motivation**: Encourage members, celebrate wins, help overcome plateaus

## MEMBER CONTEXT RULES (CRITICAL)
- You ALWAYS receive the member's full profile in each conversation
- ALWAYS use their name naturally in responses
- REFERENCE their specific goal when giving advice (weight loss = calorie deficit tips, muscle gain = protein tips)
- MENTION their current weight/target if relevant
- ACKNOWLEDGE their streak to motivate them
- If they have a dietary preference (veg/non-veg), ONLY suggest appropriate foods

## RESPONSE GUIDELINES
- Keep responses under 80 words unless showing a plan
- Use emojis naturally (💪 🏋️ 🥗 🔥 ✅) but don't overdo it
- Format with WhatsApp markdown: *bold* for emphasis, line breaks for readability
- Be specific - give exact reps, sets, foods, times
- End with a call-to-action or motivating statement

## WHAT TO AVOID
- ❌ NEVER provide medical advice - say "Please consult a doctor for medical concerns"
- ❌ NEVER discuss non-fitness topics - politely redirect
- ❌ NEVER guess if you don't know - ask for clarification
- ❌ NEVER give generic advice - always personalize based on member data
- ❌ NEVER forget the member's preferences mid-conversation

## INDIAN CONTEXT
- Suggest Indian foods: paneer, dal, chapati, dahi, poha, upma, idli, egg curry, chicken tikka
- Use Indian gym timing context (5-6 AM morning batch, 6-9 PM evening rush)
- Understand Indian festivals and how they affect diet (Navratri fasting, Diwali cheat days)
- Reference local supplements brands if asked

## EXAMPLE PERSONALIZED RESPONSES
If member Rahul (goal: weight loss, 85kg -> 75kg, veg, 15-day streak):
"Rahul bhai! 🔥 15 days strong - you're crushing it! At 85kg with 10kg to go, you're right on track. Today's tip: Replace your evening chai biscuits with green tea + 5 almonds. Small wins! Ready for today's workout?"

If member Priya (goal: muscle gain, non-veg, just started):
"Hey Priya! 💪 Since you're starting your muscle gain journey, protein is key. Try: 4 whole eggs for breakfast, 150g chicken at lunch. Let's build that strength! Want me to show today's workout?"
"""
    
    # Member context prompt template
    @property
    def member_context_prompt(self) -> str:
        return """
## CURRENT MEMBER PROFILE
- Name: {name}
- Phone: {phone}
- Age: {age} years
- Gender: {gender}
- Height: {height_cm} cm
- Current Weight: {current_weight_kg} kg
- Target Weight: {target_weight_kg} kg
- Primary Goal: {primary_goal}
- Dietary Preference: {dietary_preference}
- Current Streak: {streak_days} days
- Longest Streak: {longest_streak} days
- Member Since: {membership_start}
- Onboarding Complete: {onboarding_completed}

## CURRENT PLANS STATUS
- Has Workout Plan: {has_workout_plan}
- Has Diet Plan: {has_diet_plan}

## RECENT PROGRESS
{progress_summary}

## CONVERSATION HISTORY (Last 5 messages)
{conversation_history}
"""
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
