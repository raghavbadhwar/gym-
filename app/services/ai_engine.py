"""
AI Engine - The "Brain" of GymBot-Core

This module handles all AI-powered features:
- Intent Classification (NEW_LEAD, BOOKING, FAQ, HUMAN_HELP)
- Response Generation with guardrails
- Profanity/sentiment detection for escalation
- Ambiguity handling with confidence scores
- Natural language understanding for bookings
"""
import json
import re
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
from datetime import datetime, timedelta
from dateutil import parser as date_parser
from loguru import logger

from app.config import settings

# Intent types as specified
class Intent(str, Enum):
    NEW_LEAD = "NEW_LEAD"       # User saying hi/inquiring for first time
    BOOKING = "BOOKING"         # User wants to schedule a class
    FAQ = "FAQ"                 # User asking about price, location, hours
    HUMAN_HELP = "HUMAN_HELP"   # User frustrated or asking for manager
    GREETING = "GREETING"       # Simple hello
    WORKOUT = "WORKOUT"         # Asking about workouts
    DIET = "DIET"               # Asking about diet/nutrition
    PROGRESS = "PROGRESS"       # Checking progress/stats
    CANCEL = "CANCEL"           # Cancel booking
    GENERAL = "GENERAL"         # General fitness questions
    OFF_TOPIC = "OFF_TOPIC"     # Non-fitness topics

# Profanity and frustration indicators
PROFANITY_WORDS = [
    "damn", "hell", "crap", "suck", "stupid", "idiot", "dumb", "hate",
    "terrible", "worst", "awful", "pathetic", "useless", "ridiculous"
]

ESCALATION_PHRASES = [
    "speak to manager", "talk to human", "real person", "speak to someone",
    "call me", "supervisor", "complaint", "sue", "lawyer", "legal",
    "unsubscribe", "stop messaging", "leave me alone", "cancel membership"
]

FRUSTRATION_INDICATORS = [
    "this is ridiculous", "not working", "doesn't understand", 
    "waste of time", "frustrated", "angry", "annoyed", "fed up",
    "terrible service", "worst experience", "never again"
]


class AIEngine:
    """
    Main AI Engine for processing messages and generating responses.
    Supports both OpenAI (GPT-4o-mini) and Google Gemini.
    """
    
    def __init__(self):
        self._openai_client = None
        self._gemini_model = None
        self._initialize_ai()
    
    def _initialize_ai(self):
        """Initialize AI client based on settings."""
        if settings.ai_provider == "openai" and settings.openai_api_key:
            try:
                from openai import AsyncOpenAI
                self._openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
                logger.info("AI Engine initialized with OpenAI GPT-4o-mini")
            except ImportError:
                logger.warning("OpenAI package not installed. Run: pip install openai")
        
        elif settings.ai_provider == "gemini" and settings.gemini_api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.gemini_api_key)
                self._gemini_model = genai.GenerativeModel(settings.gemini_model)
                logger.info("AI Engine initialized with Google Gemini")
            except ImportError:
                logger.warning("Gemini package not installed. Run: pip install google-generativeai")
        
        else:
            logger.warning("No AI API key configured. Using rule-based fallback.")
    
    async def classify_intent(self, message: str, is_new_user: bool = False) -> Dict[str, Any]:
        """
        Classify user intent from message.
        
        Returns:
            {
                "intent": Intent enum value,
                "confidence": 0.0 to 1.0,
                "entities": {"class_type": "yoga", "time": "5pm", "date": "tomorrow"},
                "requires_escalation": bool,
                "ambiguous": bool
            }
        """
        message_lower = message.lower().strip()
        
        # First check for escalation indicators
        requires_escalation = self._check_escalation(message_lower)
        if requires_escalation:
            logger.warning(f"Escalation triggered for message: {message[:50]}...")
            return {
                "intent": Intent.HUMAN_HELP,
                "confidence": 0.95,
                "entities": {},
                "requires_escalation": True,
                "ambiguous": False,
                "escalation_reason": requires_escalation
            }
        
        # Check for goal-setting / substantive content BEFORE treating as new lead
        goal_keywords = ["goal", "want to", "like to", "lose weight", "lose kg", "gain muscle", 
                         "build muscle", "get fit", "be healthy", "my target", "kilos", "kgs",
                         "workout", "diet", "exercise", "help me"]
        has_goal_content = any(k in message_lower for k in goal_keywords)
        
        # If new user with just a greeting, treat as NEW_LEAD
        # But if they provide meaningful content, classify that instead
        if is_new_user and not has_goal_content:
            greetings = ["hi", "hello", "hey", "good morning", "good evening", "namaste"]
            is_simple_greeting = any(g in message_lower for g in greetings) and len(message_lower.split()) <= 6
            if is_simple_greeting:
                return {
                    "intent": Intent.NEW_LEAD,
                    "confidence": 0.9,
                    "entities": {},
                    "requires_escalation": False,
                    "ambiguous": False
                }
        
        # Try AI-based classification first
        if self._openai_client or self._gemini_model:
            return await self._ai_classify_intent(message)
        
        # Fallback to rule-based classification
        return self._rule_based_classify(message_lower)
    
    def _check_escalation(self, message: str) -> Optional[str]:
        """
        Check if message requires escalation to human.
        Returns reason if escalation needed, None otherwise.
        """
        # Check for profanity
        for word in PROFANITY_WORDS:
            if word in message:
                return f"profanity_detected: {word}"
        
        # Check for explicit escalation requests
        for phrase in ESCALATION_PHRASES:
            if phrase in message:
                return f"escalation_requested: {phrase}"
        
        # Check for frustration indicators
        for indicator in FRUSTRATION_INDICATORS:
            if indicator in message:
                return f"frustration_detected: {indicator}"
        
        # Check for excessive punctuation (frustration signal)
        if message.count("!") >= 3 or message.count("?") >= 3:
            return "excessive_punctuation"
        
        # Check for ALL CAPS (shouting)
        words = message.split()
        caps_words = sum(1 for w in words if w.isupper() and len(w) > 2)
        if caps_words >= 3:
            return "shouting_detected"
        
        return None
    
    async def _ai_classify_intent(self, message: str) -> Dict[str, Any]:
        """Use AI to classify intent."""
        prompt = f"""Classify this gym-related message into ONE of these intents:

MESSAGE: "{message}"

INTENTS:
- NEW_LEAD: First-time inquiry or interest in joining
- BOOKING: Wants to schedule/book a class (look for class names, dates, times)
- FAQ: Asking about price, location, hours, facilities, membership
- HUMAN_HELP: Frustrated, wants to speak to someone, complaints
- GREETING: Simple hello/hi
- WORKOUT: Asking about workout plans or exercises
- DIET: Asking about diet, meal plans, nutrition
- PROGRESS: Checking stats, progress, streak
- CANCEL: Wants to cancel a booking
- GENERAL: General fitness questions
- OFF_TOPIC: Not related to fitness/gym

Also extract any entities like:
- class_type: yoga, hiit, spin, strength, etc.
- date: today, tomorrow, monday, specific date
- time: 5pm, morning, 6:00 AM, etc.

Return ONLY valid JSON:
{{
    "intent": "INTENT_NAME",
    "confidence": 0.0 to 1.0,
    "entities": {{"class_type": "...", "date": "...", "time": "..."}},
    "ambiguous": true/false
}}"""

        try:
            response = await self._generate_json(prompt)
            intent_str = response.get("intent", "GENERAL")
            
            # Convert to Intent enum
            try:
                intent = Intent(intent_str)
            except ValueError:
                intent = Intent.GENERAL
            
            return {
                "intent": intent,
                "confidence": response.get("confidence", 0.7),
                "entities": response.get("entities", {}),
                "requires_escalation": False,
                "ambiguous": response.get("ambiguous", False)
            }
        except Exception as e:
            logger.error(f"AI classification failed: {e}")
            return self._rule_based_classify(message.lower())
    
    def _rule_based_classify(self, message: str) -> Dict[str, Any]:
        """Fallback rule-based intent classification."""
        # Greeting patterns (including introductions)
        greetings = ["hi", "hello", "hey", "good morning", "good evening", "namaste", "hola"]
        intro_patterns = ["i am ", "i'm ", "my name is ", "this is ", "call me "]
        
        is_greeting = any(g in message for g in greetings) and len(message.split()) <= 6
        is_intro = any(p in message for p in intro_patterns) and len(message.split()) <= 6
        
        if is_greeting or is_intro:
            return {"intent": Intent.GREETING, "confidence": 0.8, "entities": {}, 
                    "requires_escalation": False, "ambiguous": False}
        
        # Booking patterns
        booking_keywords = ["book", "schedule", "reserve", "slot", "join class", "sign up for"]
        class_types = ["yoga", "hiit", "spin", "spinning", "strength", "zumba", "aerobics", "pilates", "boxing"]
        
        if any(k in message for k in booking_keywords):
            entities = {}
            for ct in class_types:
                if ct in message:
                    entities["class_type"] = ct
                    break
            
            # Try to extract time
            time_patterns = [
                r"(\d{1,2}(?::\d{2})?\s*(?:am|pm))",
                r"(morning|afternoon|evening)",
                r"(tomorrow|today|monday|tuesday|wednesday|thursday|friday|saturday|sunday)"
            ]
            for pattern in time_patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    if "am" in match.group() or "pm" in match.group():
                        entities["time"] = match.group()
                    else:
                        entities["date"] = match.group()
            
            return {"intent": Intent.BOOKING, "confidence": 0.85, "entities": entities,
                    "requires_escalation": False, "ambiguous": not bool(entities)}
        
        # FAQ patterns
        faq_keywords = ["price", "cost", "fee", "how much", "location", "where", "address",
                        "hours", "timing", "open", "close", "facilities", "membership", 
                        "class schedule", "about classes", "types of classes"]
        if any(k in message for k in faq_keywords):
            return {"intent": Intent.FAQ, "confidence": 0.85, "entities": {},
                    "requires_escalation": False, "ambiguous": False}
        
        # Cancel patterns
        cancel_keywords = ["cancel", "unbook", "remove booking", "don't want"]
        if any(k in message for k in cancel_keywords):
            return {"intent": Intent.CANCEL, "confidence": 0.85, "entities": {},
                    "requires_escalation": False, "ambiguous": False}

        # Goal setting / Onboarding patterns - should trigger AI conversation
        goal_keywords = ["goal", "want to", "like to", "lose weight", "lose kg", "gain muscle",
                         "build muscle", "get fit", "be healthy", "my target", "kilos", "kgs",
                         "didn't tell", "didnt tell", "haven't told", "havent told"]
        if any(k in message for k in goal_keywords):
            return {"intent": Intent.GENERAL, "confidence": 0.9, "entities": {},
                    "requires_escalation": False, "ambiguous": False}  # High confidence = go to AI

        # Workout patterns
        workout_keywords = ["workout", "exercise", "routine", "training", "today's workout", "gym"]
        if any(k in message for k in workout_keywords):
            return {"intent": Intent.WORKOUT, "confidence": 0.85, "entities": {},
                    "requires_escalation": False, "ambiguous": False}
        
        # Diet patterns
        diet_keywords = ["diet", "meal", "food", "nutrition", "eat", "calories", "protein", "dinner", "lunch", "breakfast"]
        if any(k in message for k in diet_keywords):
            return {"intent": Intent.DIET, "confidence": 0.85, "entities": {},
                    "requires_escalation": False, "ambiguous": False}
        
        # Progress patterns
        progress_keywords = ["progress", "stats", "weight", "streak", "how am i doing"]
        if any(k in message for k in progress_keywords):
            return {"intent": Intent.PROGRESS, "confidence": 0.85, "entities": {},
                    "requires_escalation": False, "ambiguous": False}
        
        # Default to general with HIGH confidence - ALWAYS use AI for unknown messages
        return {"intent": Intent.GENERAL, "confidence": 0.9, "entities": {},
                "requires_escalation": False, "ambiguous": False}
    
    async def generate_response(
        self,
        message: str,
        intent: Intent,
        context: Dict[str, Any] = None
    ) -> str:
        """
        Generate AI response with guardrails and full member context.
        
        Args:
            message: User's message
            intent: Classified intent
            context: Full member context including:
                - member_name, member_goal, weight, target_weight
                - dietary_preference, streak, height, age, gender
                - conversation_history, progress
        
        Returns:
            Generated response string
        """
        if not (self._openai_client or self._gemini_model):
            return self._get_fallback_response(intent)
        
        # Build comprehensive member context
        member_context = ""
        if context:
            member_context = f"""
## MEMBER PROFILE (Use this to personalize your response!)
- Name: {context.get('member_name', 'Member')}
- Primary Goal: {context.get('member_goal', 'general fitness')}
- Current Weight: {context.get('weight', 'Not specified')} kg
- Target Weight: {context.get('target_weight', 'Not specified')} kg
- Height: {context.get('height', 'Not specified')} cm
- Age: {context.get('age', 'Not specified')} years
- Gender: {context.get('gender', 'Not specified')}
- Dietary Preference: {context.get('dietary_preference', 'Not specified')}
- Current Streak: {context.get('streak', 0)} days
- Experience Level: {context.get('experience_level', 'beginner')}

## MEMBER PROGRESS
{context.get('progress_summary', 'No progress data yet')}

## CONVERSATION HISTORY (Last messages for context)
{context.get('conversation_history', 'First conversation with this member')}
"""
        
        prompt = f"""{settings.system_prompt}

{member_context}

## CURRENT MESSAGE
User says: "{message}"
Detected Intent: {intent.value}

## YOUR TASK
Generate a personalized, helpful response that:
1. Uses the member's NAME naturally
2. References their GOAL when giving advice
3. Acknowledges their STREAK if impressive (5+ days)
4. Respects their DIETARY PREFERENCE (veg/non-veg)
5. Is specific to their WEIGHT/TARGET if relevant
6. Keeps the response under 80 words unless showing a plan

Response:"""

        try:
            response = await self._generate_text(prompt)
            # Apply guardrails check on response
            if self._is_off_topic_response(response):
                name = context.get('member_name', '') if context else ''
                return f"{'Hey ' + name + '! ' if name else ''}I'm your gym assistant, so I'm best at helping with fitness topics! 💪 Is there anything gym-related I can help you with?"
            return response
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            return self._get_fallback_response(intent, message=message)
    
    def _is_off_topic_response(self, response: str) -> bool:
        """Check if response strayed off-topic."""
        off_topic_indicators = [
            "as an ai", "i cannot", "i don't have access to",
            "weather", "stock", "news", "politics", "recipe"
        ]
        response_lower = response.lower()
        return any(ind in response_lower for ind in off_topic_indicators)
    
    def _get_fallback_response(self, intent: Intent, message: str = "") -> str:
        """Get fallback response when AI is unavailable."""
        
        # If intent is GENERAL but message clearly asks for something, try to give specific help
        if intent == Intent.GENERAL and message:
            msg_lower = message.lower()
            if "class" in msg_lower or "schedule" in msg_lower:
                return "Our classes include Yoga, HIIT, Spin, and Boxing! 📅 Reply 'book' to see the schedule or book a spot."
            if "diet" in msg_lower or "food" in msg_lower or "eat" in msg_lower:
                return "Nutrition is key! 🥗 Reply 'diet' to get your personalized meal plan."
            if "workout" in msg_lower or "exercise" in msg_lower or "gym" in msg_lower:
                return "Ready to sweat? 💪 Reply 'workout' for your daily routine."
            if "goal" in msg_lower or "weight" in msg_lower or "fat" in msg_lower:
                return "I can help you reach your goals! 🎯 Tell me your target weight or reply 'update goal'."

        responses = {
            Intent.NEW_LEAD: f"Welcome to {settings.gym_name}! 👋 I'm your virtual assistant. Are you looking to join or just visiting?",
            Intent.BOOKING: "I'd love to help you book a class! 📅 Which class interests you? We have Yoga, HIIT, Spin, and more!",
            Intent.FAQ: f"Great question! {settings.gym_name} is open 6 AM - 10 PM. For pricing and location details, reply 'pricing' or 'location'.",
            Intent.HUMAN_HELP: "I'm passing this to a human manager. They will text you shortly. 🙏",
            Intent.GREETING: f"Hey there! 👋 Welcome to {settings.gym_name}! What can I help you with today?",
            Intent.WORKOUT: "Ready to crush it! 💪 Reply 'workout' to get today's personalized workout plan!",
            Intent.DIET: "Let's fuel that body right! 🥗 Reply 'diet' for your personalized meal plan!",
            Intent.PROGRESS: "Let's check your progress! 📊 Reply 'stats' to see how far you've come!",
            Intent.CANCEL: "No problem! To cancel a booking, let me know which class you'd like to cancel.",
            Intent.GENERAL: "I'm here to help with all things fitness! 💪 Ask me about workouts, diet, classes, or bookings!",
            Intent.OFF_TOPIC: "I'm your gym assistant, so I'm best at helping with fitness topics! 💪 Is there anything gym-related I can help you with?"
        }
        return responses.get(intent, responses[Intent.GENERAL])
    
    async def parse_booking_details(self, message: str) -> Dict[str, Any]:
        """
        Parse booking details from natural language.
        
        Examples:
        - "Yoga tomorrow at 5pm" -> {"class": "yoga", "date": tomorrow, "time": "17:00"}
        - "Book HIIT for Monday morning" -> {"class": "hiit", "date": monday, "time": "morning"}
        
        Returns:
            {
                "class_name": str,
                "booking_time": datetime or None,
                "time_description": str,
                "parsed_successfully": bool
            }
        """
        if self._openai_client or self._gemini_model:
            return await self._ai_parse_booking(message)
        return self._rule_based_parse_booking(message)
    
    async def _ai_parse_booking(self, message: str) -> Dict[str, Any]:
        """Use AI to parse booking details."""
        today = datetime.now()
        prompt = f"""Parse this booking request and extract details.

MESSAGE: "{message}"
TODAY'S DATE: {today.strftime('%Y-%m-%d')} ({today.strftime('%A')})

Extract:
1. class_name: The type of class (yoga, hiit, spin, strength, zumba, pilates, etc.)
2. date: The date in YYYY-MM-DD format
3. time: The time in HH:MM format (24-hour)
4. time_description: Human-readable time (e.g., "tomorrow at 5 PM")

Return ONLY valid JSON:
{{
    "class_name": "yoga",
    "date": "2026-01-13",
    "time": "17:00",
    "time_description": "tomorrow at 5 PM",
    "parsed_successfully": true
}}

If you cannot parse the details, return:
{{
    "class_name": null,
    "date": null,
    "time": null,
    "time_description": null,
    "parsed_successfully": false
}}"""

        try:
            result = await self._generate_json(prompt)
            
            # Convert to datetime if parsed
            if result.get("parsed_successfully") and result.get("date") and result.get("time"):
                try:
                    booking_time = datetime.strptime(
                        f"{result['date']} {result['time']}", 
                        "%Y-%m-%d %H:%M"
                    )
                    result["booking_time"] = booking_time
                except ValueError:
                    result["booking_time"] = None
            else:
                result["booking_time"] = None
            
            return result
        except Exception as e:
            logger.error(f"AI booking parsing failed: {e}")
            return self._rule_based_parse_booking(message)
    
    def _rule_based_parse_booking(self, message: str) -> Dict[str, Any]:
        """Fallback rule-based booking parser."""
        message_lower = message.lower()
        result = {
            "class_name": None,
            "booking_time": None,
            "time_description": None,
            "parsed_successfully": False
        }
        
        # Extract class type
        class_types = {
            "yoga": ["yoga", "hatha", "vinyasa"],
            "hiit": ["hiit", "high intensity", "interval"],
            "spin": ["spin", "spinning", "cycle", "cycling"],
            "strength": ["strength", "weight", "lifting", "weights"],
            "zumba": ["zumba", "dance"],
            "pilates": ["pilates", "core"],
            "aerobics": ["aerobics", "cardio"]
        }
        
        for class_name, keywords in class_types.items():
            if any(kw in message_lower for kw in keywords):
                result["class_name"] = class_name
                break
        
        # Extract date
        today = datetime.now()
        date = None
        
        if "today" in message_lower:
            date = today.date()
        elif "tomorrow" in message_lower:
            date = (today + timedelta(days=1)).date()
        else:
            # Try to parse day names
            days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
            for i, day in enumerate(days):
                if day in message_lower:
                    # Find next occurrence of this day
                    current_weekday = today.weekday()
                    days_ahead = i - current_weekday
                    if days_ahead <= 0:
                        days_ahead += 7
                    date = (today + timedelta(days=days_ahead)).date()
                    break
        
        # Extract time
        time = None
        time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)', message_lower)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2) or 0)
            period = time_match.group(3)
            
            if period == "pm" and hour != 12:
                hour += 12
            elif period == "am" and hour == 12:
                hour = 0
            
            time = f"{hour:02d}:{minute:02d}"
        elif "morning" in message_lower:
            time = "06:00"
        elif "afternoon" in message_lower:
            time = "14:00"
        elif "evening" in message_lower:
            time = "18:00"
        
        # Combine into datetime
        if date and time:
            try:
                booking_time = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
                result["booking_time"] = booking_time
                result["time_description"] = booking_time.strftime("%A at %I:%M %p")
                result["parsed_successfully"] = True
            except ValueError:
                pass
        
        return result
    
    def get_ambiguity_response(self, intent: Intent, entities: Dict) -> str:
        """Generate clarification response for ambiguous requests."""
        if intent == Intent.BOOKING:
            missing = []
            if not entities.get("class_type"):
                missing.append("class type")
            if not entities.get("date"):
                missing.append("date")
            if not entities.get("time"):
                missing.append("time")
            
            if missing:
                return f"I want to make sure I get this right. 🤔 Could you tell me the {', '.join(missing)}? For example: 'Yoga tomorrow at 5pm'"
        
        return "I want to make sure I get this right. Did you mean:\n\n🏋️ *Book a class* - Schedule a workout\n📊 *Check progress* - See your stats\n❓ *Get info* - Prices, hours, location"
    
    def get_escalation_response(self) -> str:
        """Response when escalating to human."""
        return "I'm passing this to a human manager. They will text you shortly. 🙏\n\nIn the meantime, is there anything else I can help with?"
    
    def get_media_response(self, media_type: str) -> str:
        """Response for unsupported media types."""
        return f"I can only read text for now! 📝 Please type your request.\n\nNeed help? Just say 'help' to see what I can do!"
    
    async def _generate_json(self, prompt: str) -> Dict:
        """Generate JSON response from AI."""
        if self._openai_client:
            response = await self._openai_client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that responds only in valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            text = response.choices[0].message.content.strip()
        elif self._gemini_model:
            response = await self._gemini_model.generate_content_async(prompt)
            text = response.text.strip()
        else:
            raise ValueError("No AI provider configured")
        
        # Clean up response
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text.rsplit("\n", 1)[0]
        if text.startswith("json"):
            text = text[4:].strip()
        
        return json.loads(text)
    
    async def _generate_text(self, prompt: str) -> str:
        """Generate text response from AI with retry for rate limits."""
        import asyncio
        
        if self._openai_client:
            response = await self._openai_client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": settings.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=150
            )
            return response.choices[0].message.content.strip()
        elif self._gemini_model:
            # Retry logic for rate limits
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = await self._gemini_model.generate_content_async(prompt)
                    return response.text.strip()
                except Exception as e:
                    error_str = str(e).lower()
                    if "quota" in error_str or "rate" in error_str or "429" in error_str:
                        wait_time = (attempt + 1) * 2  # 2, 4, 6 seconds
                        logger.warning(f"Rate limit hit, waiting {wait_time}s (attempt {attempt + 1}/{max_retries})")
                        await asyncio.sleep(wait_time)
                    else:
                        raise  # Re-raise non-rate-limit errors
            # If all retries failed, raise
            raise ValueError("Gemini API rate limit exceeded after retries")
        else:
            raise ValueError("No AI provider configured")


# Singleton instance
ai_engine = AIEngine()
