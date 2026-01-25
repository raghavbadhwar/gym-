"""
Message Handler - Main entry point for processing WhatsApp messages

Routes messages to appropriate flows based on:
- Intent classification (NEW_LEAD, BOOKING, FAQ, HUMAN_HELP, etc.)
- Conversation state (ongoing flows)
- Member status (new vs returning)
"""
from typing import Dict, Any, Optional, Union
from sqlalchemy.orm import Session
from loguru import logger

from app.services.member_service import MemberService
from app.services.workout_service import WorkoutService
from app.services.diet_service import DietService
from app.services.booking_service import BookingService
from app.services.ai_engine import ai_engine, Intent
from app.flows.onboarding import OnboardingFlow
from app.flows.booking import BookingFlow
from app.config import settings


class MessageHandler:
    """
    Main handler for processing incoming WhatsApp messages.
    Routes messages to appropriate flows based on context and intent.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.member_service = MemberService(db)
        self.workout_service = WorkoutService(db)
        self.diet_service = DietService(db)
        self.booking_service = BookingService(db)
        self.onboarding_flow = OnboardingFlow(db)
        self.booking_flow = BookingFlow(db)
    
    async def handle(self, message: Dict[str, Any]) -> Optional[Union[str, Dict]]:
        """
        Main message handler. Routes to appropriate flow or handles directly.
        
        Args:
            message: Parsed message dict with keys:
                - from: Phone number
                - name: Contact name
                - type: Message type (text, interactive, etc.)
                - content: Message content
        
        Returns:
            Response to send back (str or dict for rich responses)
        """
        phone = message["from"]
        content = message.get("content", "").strip()
        name = message.get("name", "there")
        
        logger.info(f"📨 Handling message from {phone}: {content[:50]}...")
        
        # Get or create member
        member = self.member_service.get_by_phone(phone)
        
        # Check if in active flow
        conv_state = self.member_service.get_conversation_state(phone)
        
        if conv_state and conv_state.current_flow:
            # Continue existing flow
            return await self._continue_flow(conv_state, member, message)
        
        # New member - start onboarding (NEW_LEAD workflow)
        if not member:
            return await self._start_onboarding(phone, name)
        
        # Incomplete onboarding - resume
        if not member.onboarding_completed:
            return await self.onboarding_flow.resume(member, message)
        
        # Active member - classify intent and handle
        return await self._handle_active_member(member, message)
    
    async def _start_onboarding(self, phone: str, name: str) -> Dict:
        """
        Start onboarding flow for new member.
        
        NEW_LEAD Workflow:
        1. Create record in DB
        2. Welcome message
        3. Ask about joining
        """
        logger.info(f"🆕 New lead detected: {phone}")
        
        # Create member with just phone
        member = self.member_service.create(
            phone=phone,
            name=name if name != "Unknown" else "New Member"
        )
        
        # Start onboarding flow
        return await self.onboarding_flow.start(member)
    
    async def _continue_flow(
        self,
        conv_state,
        member,
        message: Dict
    ) -> Optional[Union[str, Dict]]:
        """Continue an active conversation flow."""
        flow = conv_state.current_flow
        
        if flow == "onboarding":
            return await self.onboarding_flow.handle_step(conv_state, member, message)
        elif flow == "booking":
            return await self.booking_flow.handle_step(conv_state, member, message)
        elif flow == "checkin":
            return await self._handle_checkin_flow(conv_state, member, message)
        elif flow == "escalated":
            # Flow was escalated, let them know
            return "A manager is looking into your request. Is there anything else I can help with in the meantime? 🏋️"
        else:
            # Unknown flow, clear and handle normally
            self.member_service.clear_conversation_state(message["from"])
            return await self._handle_active_member(member, message)
    
    async def _handle_active_member(
        self,
        member,
        message: Dict
    ) -> Optional[Union[str, Dict]]:
        """Handle message from active member (not in any flow)."""
        content = message.get("content", "").strip()
        content_lower = content.lower()
        
        # Check for button responses first
        if content.startswith("goal_") or content.startswith("diet_"):
            return await self.onboarding_flow.resume(member, message)
        
        # Classify intent using AI Engine
        intent_result = await ai_engine.classify_intent(content, is_new_user=False)
        intent = intent_result.get("intent", Intent.GENERAL)
        confidence = intent_result.get("confidence", 0.5)
        entities = intent_result.get("entities", {})
        
        logger.info(f"🧠 Intent: {intent.value} (confidence: {confidence:.2f})")
        
        # Route based on intent
        if intent == Intent.GREETING:
            return await self._handle_greeting(member)
        
        elif intent == Intent.BOOKING:
            # Start booking flow with initial message for parsing
            return await self.booking_flow.start(member, initial_message=content)
        
        elif intent == Intent.FAQ:
            return await self._handle_faq(member, content)
        
        elif intent == Intent.HUMAN_HELP:
            # This should be caught by webhook, but handle here too
            return ai_engine.get_escalation_response()
        
        elif intent == Intent.WORKOUT:
            return await self._handle_get_workout(member)
        
        elif intent == Intent.DIET:
            return await self._handle_get_diet(member)
        
        elif intent == Intent.PROGRESS:
            return await self._handle_progress(member)
        
        elif intent == Intent.CANCEL:
            return await self._handle_cancel_booking(member)
        
        elif intent == Intent.GENERAL:
            # General fitness questions - use AI to generate response
            response = await ai_engine.generate_response(
                content, 
                intent,
                context={
                    "member_name": member.name,
                    "member_goal": member.primary_goal.value if member.primary_goal else None
                }
            )
            return response
        
        elif intent == Intent.OFF_TOPIC:
            # Guardrail: redirect to gym topics
            return "I'm your gym assistant, so I'm best at helping with fitness topics! 💪\n\nTry asking about:\n• *workout* - Today's workout\n• *diet* - Meal plan\n• *classes* - Book a class\n• *progress* - Your stats"
        
        else:
            return self._get_help_message(member)
    
    async def _handle_greeting(self, member) -> str:
        """Handle greeting messages."""
        streak_msg = ""
        if member.streak_days > 0:
            streak_msg = f"\n\n🔥 You're on a *{member.streak_days}-day streak*! Keep it up!"
        
        return f"""Hey {member.name}! 👋

Great to see you! What would you like to do?

💪 *workout* - Today's workout
🍎 *diet* - Your meal plan
📅 *classes* - Book a class
📊 *progress* - Check your stats

Or just tell me what you need!{streak_msg}"""
    
    async def _handle_faq(self, member, content: str) -> str:
        """Handle FAQ questions (price, location, hours)."""
        content_lower = content.lower()
        
        if any(w in content_lower for w in ["price", "cost", "fee", "how much", "membership"]):
            return f"""💰 *Membership Pricing*

{settings.gym_name} offers flexible plans:

• *Monthly*: ₹2,999/month
• *Quarterly*: ₹7,999 (Save 11%)
• *Annual*: ₹24,999 (Save 30%)

All plans include:
✅ Full gym access
✅ Group classes
✅ Locker facility
✅ Personal trainer consultation

Reply *join* to start your fitness journey! 🏋️"""
        
        elif any(w in content_lower for w in ["location", "where", "address", "directions"]):
            return f"""📍 *{settings.gym_name} Location*

123 Fitness Street
Near Central Mall, 2nd Floor
Bangalore - 560001

📞 Contact: {settings.gym_phone}

🚗 Parking available in basement
🚇 Nearest metro: Central Station (5 min walk)

See you there! 💪"""
        
        elif any(w in content_lower for w in ["hours", "timing", "open", "close", "when"]):
            return f"""⏰ *{settings.gym_name} Hours*

*Monday - Saturday*
🌅 Morning: 5:00 AM - 11:00 AM
🌆 Evening: 4:00 PM - 10:00 PM

*Sunday*
🌅 Morning: 6:00 AM - 12:00 PM
(Evening closed)

*Holidays*
⚠️ Check our notice board for holiday hours

Best time to avoid crowds: 📊
• Mornings: 6-7 AM
• Evenings: 8-9 PM"""
        
        elif any(w in content_lower for w in ["facilities", "equipment", "amenities"]):
            return f"""🏋️ *{settings.gym_name} Facilities*

💪 *Strength Zone*
- Free weights (2-50 kg)
- Cable machines
- Power racks

🏃 *Cardio Zone*
- Treadmills
- Cross trainers
- Spin bikes

🧘 *Studios*
- Yoga studio
- Aerobics hall
- CrossFit area

*Amenities*
🚿 Showers & lockers
💧 RO water
🧴 Towel service
🅿️ Free parking"""
        
        else:
            return f"""❓ *How can I help?*

Here's what I can tell you about {settings.gym_name}:

💰 *pricing* - Membership costs
📍 *location* - How to find us  
⏰ *hours* - Opening times
🏋️ *facilities* - What we offer

Just ask! 😊"""
    
    async def _handle_get_workout(self, member) -> str:
        """Get today's workout for member."""
        workout = self.workout_service.get_todays_workout(member)
        
        if workout:
            return self.workout_service.format_workout_for_whatsapp(workout)
        
        # No workout plan - generate one
        plan = await self.workout_service.generate_plan(member, week_number=1)
        workout = self.workout_service.get_todays_workout(member)
        return self.workout_service.format_workout_for_whatsapp(workout)
    
    async def _handle_get_diet(self, member) -> str:
        """Get diet plan for member."""
        plan = self.diet_service.get_current_plan(member.id)
        
        if plan:
            return self.diet_service.format_plan_for_whatsapp(plan)
        
        # Generate new plan
        plan = await self.diet_service.generate_plan(member, week_number=1)
        return self.diet_service.format_plan_for_whatsapp(plan)
    
    async def _handle_progress(self, member) -> str:
        """Show progress summary."""
        summary = self.workout_service.get_progress_summary(member)
        return self.workout_service.format_progress_for_whatsapp(member, summary)
    
    async def _handle_cancel_booking(self, member) -> str:
        """Show bookings to cancel."""
        bookings = self.booking_service.get_member_bookings(member)
        
        if not bookings:
            return "You don't have any upcoming bookings to cancel.\n\nSend *classes* to view the schedule!"
        
        return self.booking_service.format_member_bookings(bookings)
    
    async def _handle_checkin_flow(self, conv_state, member, message) -> Union[str, Dict]:
        """Handle weekly check-in flow."""
        step = conv_state.current_step
        content = message.get("content", "").strip()
        flow_data = conv_state.flow_data or {}
        
        if step == "weight":
            try:
                weight = float(content.replace("kg", "").strip())
                flow_data["weight"] = weight
                self.member_service.set_conversation_state(
                    member.phone, "checkin", "energy", flow_data
                )
                return {
                    "type": "buttons",
                    "body": f"Got it! {weight} kg recorded.\n\nHow's your energy level this week?",
                    "buttons": [
                        {"id": "energy_1", "title": "1 - Low 😴"},
                        {"id": "energy_3", "title": "3 - Ok 😊"},
                        {"id": "energy_5", "title": "5 - Great 🔥"}
                    ]
                }
            except ValueError:
                return "Please enter your weight as a number (e.g., 72.5 or 72.5kg)"
        
        elif step == "energy":
            if content.startswith("energy_"):
                energy = int(content.split("_")[1])
            else:
                try:
                    energy = int(content)
                except ValueError:
                    return "Please select an energy level or type a number 1-5"
            
            flow_data["energy"] = energy
            self.member_service.set_conversation_state(
                member.phone, "checkin", "compliance", flow_data
            )
            return {
                "type": "buttons",
                "body": "How well did you follow your diet plan this week?",
                "buttons": [
                    {"id": "diet_full", "title": "Fully ✅"},
                    {"id": "diet_mostly", "title": "Mostly 👍"},
                    {"id": "diet_poor", "title": "Struggled 😅"}
                ]
            }
        
        elif step == "compliance":
            if content.startswith("diet_"):
                compliance = content.replace("diet_", "")
            else:
                compliance = "mostly"
            
            # Record check-in
            self.workout_service.record_checkin(
                member,
                weight_kg=flow_data.get("weight"),
                energy_level=flow_data.get("energy"),
                diet_compliance=compliance
            )
            
            # Clear flow
            self.member_service.clear_conversation_state(member.phone)
            
            # Get progress summary
            summary = self.workout_service.get_progress_summary(member)
            
            return f"""✅ *Check-in Complete!*

{self.workout_service.format_progress_for_whatsapp(member, summary)}

Your plan has been updated based on your progress!"""
        
        return "Something went wrong. Let's start over. Reply *checkin* when ready."
    
    def _get_help_message(self, member) -> str:
        """Get help message with available commands."""
        return f"""*Hi {member.name}! Here's what I can do:* 🤖

💪 *workout* - Get today's workout
🍎 *diet* - View your meal plan  
📅 *classes* or *book* - Book a class
📊 *progress* - See your stats
🔥 *streak* - Check your streak
✅ *done* - Log completed workout
📝 *checkin* - Weekly check-in
❌ *cancel* - Cancel a booking

*Quick FAQs:*
💰 *pricing* - Membership costs
📍 *location* - How to find us
⏰ *hours* - Opening times

Just type any of these or describe what you need!"""
