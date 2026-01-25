"""
Booking Flow - Class booking via WhatsApp

Handles:
- Natural language booking requests ("Yoga tomorrow at 5pm")
- Interactive class selection with lists
- Booking confirmation
- Double-booking prevention feedback
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Union
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_
from loguru import logger

from app.services.member_service import MemberService
from app.services.booking_service import BookingService
from app.services.ai_engine import ai_engine
from app.models.booking import Class


class BookingFlow:
    """
    Handles class booking flow via WhatsApp.
    Shows available classes -> Select class -> Confirm booking
    
    Supports natural language booking:
    - "Book yoga tomorrow at 5pm"
    - "I want to join HIIT on Monday"
    """
    
    FLOW_NAME = "booking"
    
    def __init__(self, db: Session):
        self.db = db
        self.member_service = MemberService(db)
        self.booking_service = BookingService(db)
    
    async def start(self, member, initial_message: str = None) -> Union[str, Dict]:
        """
        Start booking flow.
        
        If initial_message contains booking details, try to parse and book directly.
        Otherwise, show available classes.
        """
        # Try to parse natural language booking request
        if initial_message:
            parsed = await ai_engine.parse_booking_details(initial_message)
            
            if parsed.get("parsed_successfully"):
                logger.info(f"Parsed booking: {parsed}")
                
                # Try to find matching class
                matching_class = self._find_matching_class(
                    class_name=parsed.get("class_name"),
                    booking_time=parsed.get("booking_time")
                )
                
                if matching_class:
                    # Store and ask for confirmation
                    self.member_service.set_conversation_state(
                        phone=member.phone,
                        flow=self.FLOW_NAME,
                        step="confirm",
                        data={"selected_class_id": str(matching_class.id)}
                    )
                    return self._get_confirmation_message(matching_class)
                else:
                    # No exact match, show suggestions
                    return await self._suggest_similar_classes(member, parsed)
        
        # Default: show class list
        return await self._show_class_list(member)
    
    def _find_matching_class(
        self,
        class_name: str = None,
        booking_time: datetime = None
    ) -> Optional[Class]:
        """Find a class matching the parsed criteria."""
        query = self.db.query(Class).filter(
            and_(
                Class.scheduled_at >= datetime.utcnow(),
                Class.is_cancelled == False
            )
        )
        
        # Filter by time if provided
        if booking_time:
            # Allow 30 minute window
            time_start = booking_time - timedelta(minutes=30)
            time_end = booking_time + timedelta(minutes=30)
            query = query.filter(
                Class.scheduled_at.between(time_start, time_end)
            )
        
        # Filter by class type/name if provided
        if class_name:
            query = query.filter(
                (Class.class_type.ilike(f"%{class_name}%")) |
                (Class.name.ilike(f"%{class_name}%"))
            )
        
        return query.order_by(Class.scheduled_at).first()
    
    async def _suggest_similar_classes(
        self,
        member,
        parsed: Dict
    ) -> Union[str, Dict]:
        """Suggest similar classes when exact match not found."""
        class_name = parsed.get("class_name", "")
        time_desc = parsed.get("time_description", "")
        
        # Find similar classes
        query = self.db.query(Class).filter(
            and_(
                Class.scheduled_at >= datetime.utcnow(),
                Class.is_cancelled == False
            )
        )
        
        if class_name:
            query = query.filter(
                (Class.class_type.ilike(f"%{class_name}%")) |
                (Class.name.ilike(f"%{class_name}%"))
            )
        
        similar_classes = query.order_by(Class.scheduled_at).limit(5).all()
        
        if similar_classes:
            # Store classes for selection
            self.member_service.set_conversation_state(
                phone=member.phone,
                flow=self.FLOW_NAME,
                step="select_class",
                data={"classes": [str(c.id) for c in similar_classes]}
            )
            
            lines = [f"🤔 I couldn't find an exact match for *{class_name}* {time_desc}."]
            lines.append("Here are some similar options:\n")
            
            for c in similar_classes:
                time_str = c.scheduled_at.strftime("%a %I:%M %p").lstrip("0")
                slots = c.available_slots
                status = f"✅ {slots} spots" if slots > 0 else "⏳ Waitlist"
                lines.append(f"• *{c.name}* - {time_str} ({status})")
            
            lines.append("\nReply with the class name to book!")
            return "\n".join(lines)
        
        # No similar classes found
        return f"😕 I couldn't find any {class_name} classes scheduled. Would you like to see all available classes? Reply *classes* to view the schedule."
    
    async def _show_class_list(self, member) -> Union[str, Dict]:
        """Show list of available classes."""
        # Get upcoming classes
        classes = self.booking_service.get_upcoming_classes(days=3)
        
        if not classes:
            return "No classes scheduled for the next few days. Check back later! 📅"
        
        # Set conversation state
        self.member_service.set_conversation_state(
            phone=member.phone,
            flow=self.FLOW_NAME,
            step="select_class",
            data={"classes": [str(c.id) for c in classes[:10]]}
        )
        
        # Build list sections by date
        sections = []
        current_date = None
        current_rows = []
        
        for c in classes[:10]:  # Max 10 classes in list
            class_date = c.scheduled_at.date()
            
            if class_date != current_date:
                if current_rows:
                    sections.append({
                        "title": current_date.strftime("%A, %b %d"),
                        "rows": current_rows
                    })
                current_date = class_date
                current_rows = []
            
            time_str = c.scheduled_at.strftime("%I:%M %p").lstrip("0")
            slots = c.available_slots
            status = f"✅ {slots} spots" if slots > 0 else "⏳ Waitlist"
            
            current_rows.append({
                "id": f"class_{c.id}",
                "title": f"{time_str} - {c.name}"[:24],
                "description": f"{c.trainer_name} | {status}"[:72]
            })
        
        # Add last section
        if current_rows:
            sections.append({
                "title": current_date.strftime("%A, %b %d"),
                "rows": current_rows
            })
        
        return {
            "type": "list",
            "header": "📅 Class Schedule",
            "body": "Select a class to book. I'll save your spot and remind you!\n\nTap the button below to see available classes.",
            "button_text": "View Classes",
            "sections": sections,
            "footer": "Showing next 3 days"
        }
    
    def _get_confirmation_message(self, gym_class: Class) -> Dict:
        """Get confirmation message for a class."""
        time_str = gym_class.scheduled_at.strftime("%A, %B %d at %I:%M %p").lstrip("0")
        slots = gym_class.available_slots
        
        if slots > 0:
            status_msg = f"✅ {slots} spots available"
        else:
            status_msg = f"⏳ Class is full - you'll be added to waitlist (position #{gym_class.waitlist_count + 1})"
        
        return {
            "type": "buttons",
            "body": f"""*{gym_class.name}*

📅 {time_str}
👤 Trainer: {gym_class.trainer_name}
⏱️ Duration: {gym_class.duration_mins} minutes
🏠 Location: {gym_class.room or 'Main Floor'}
🔥 Intensity: {gym_class.intensity.title()}

{status_msg}

*Confirm booking?*""",
            "buttons": [
                {"id": "book_confirm", "title": "Book Now ✅"},
                {"id": "book_cancel", "title": "Cancel ❌"}
            ]
        }
    
    async def handle_step(
        self,
        conv_state,
        member,
        message: Dict
    ) -> Optional[Union[str, Dict]]:
        """
        Handle a step in the booking flow.
        """
        step = conv_state.current_step
        content = message.get("content", "").strip()
        flow_data = conv_state.flow_data or {}
        
        logger.info(f"Booking step: {step}, content: {content}")
        
        if step == "select_class":
            return await self._handle_class_selection(member, content, flow_data)
        
        elif step == "confirm":
            return await self._handle_confirmation(member, content, flow_data)
        
        else:
            # Unknown step, restart
            return await self.start(member)
    
    async def _handle_class_selection(
        self,
        member,
        content: str,
        flow_data: dict
    ) -> Union[str, Dict]:
        """Handle class selection from list or natural language."""
        class_id = None
        
        # Check if it's a list reply with class ID
        if content.startswith("class_"):
            class_id = content.replace("class_", "")
        
        # Try to find class by name/time in content
        if not class_id:
            classes = self.booking_service.get_upcoming_classes(days=3)
            content_lower = content.lower()
            
            for c in classes:
                if c.name.lower() in content_lower:
                    class_id = str(c.id)
                    break
                time_str = c.scheduled_at.strftime("%I:%M").lstrip("0").lower()
                if time_str in content_lower:
                    class_id = str(c.id)
                    break
        
        if not class_id:
            # Couldn't identify class, try AI parsing
            parsed = await ai_engine.parse_booking_details(content)
            if parsed.get("parsed_successfully"):
                matching_class = self._find_matching_class(
                    class_name=parsed.get("class_name"),
                    booking_time=parsed.get("booking_time")
                )
                if matching_class:
                    class_id = str(matching_class.id)
        
        if not class_id:
            # Still couldn't find, show list again
            return await self._show_class_list(member)
        
        # Get class details
        gym_class = self.booking_service.get_class(UUID(class_id))
        if not gym_class:
            return "Couldn't find that class. Let me show you the schedule again."
        
        # Store selected class and ask for confirmation
        flow_data["selected_class_id"] = class_id
        self.member_service.set_conversation_state(
            member.phone, self.FLOW_NAME, "confirm", flow_data
        )
        
        return self._get_confirmation_message(gym_class)
    
    async def _handle_confirmation(
        self,
        member,
        content: str,
        flow_data: dict
    ) -> Union[str, Dict]:
        """Handle booking confirmation."""
        content_lower = content.lower()
        
        # Check for cancel
        if "cancel" in content_lower or "no" in content_lower or "book_cancel" in content:
            self.member_service.clear_conversation_state(member.phone)
            return "No problem! Let me know when you want to book a class. 📅"
        
        # Confirm booking
        if "confirm" in content_lower or "yes" in content_lower or "book_confirm" in content or "book" in content:
            class_id = flow_data.get("selected_class_id")
            
            if not class_id:
                self.member_service.clear_conversation_state(member.phone)
                return "Something went wrong. Please try booking again."
            
            # Make the booking
            result = self.booking_service.book_class(member, UUID(class_id))
            
            # Clear flow
            self.member_service.clear_conversation_state(member.phone)
            
            # Check for double-booking conflict
            if not result["success"] and result.get("conflict"):
                conflict = result["conflict"]
                return f"""⚠️ *Booking Conflict!*

You already have *{conflict['class_name']}* booked at the same time.

Cancel that booking first, or choose a different class.

Reply *classes* to see other options."""
            
            # Return confirmation message
            return self.booking_service.format_booking_confirmation(result)
        
        # Unclear response
        return {
            "type": "buttons",
            "body": "Would you like to confirm this booking?",
            "buttons": [
                {"id": "book_confirm", "title": "Yes, Book ✅"},
                {"id": "book_cancel", "title": "No, Cancel ❌"}
            ]
        }
