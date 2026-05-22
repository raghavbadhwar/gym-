"""
Booking Service - Class booking and scheduling management

Handles class creation, booking, cancellation, and
double-booking prevention as specified in requirements.
"""
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session, contains_eager
from sqlalchemy import and_, func
from loguru import logger

from app.models.booking import Class, ClassBooking, BookingStatus
from app.models.member import Member


class BookingService:
    """
    Service for class scheduling and booking management.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    # ========== Class Management ==========
    
    def create_class(
        self,
        name: str,
        class_type: str,
        trainer_name: str,
        scheduled_at: datetime,
        duration_mins: int = 45,
        capacity: int = 20,
        room: str = None,
        intensity: str = "medium",
        goal_tags: List[str] = None
    ) -> Class:
        """Create a new class session."""
        gym_class = Class(
            name=name,
            class_type=class_type,
            trainer_name=trainer_name,
            scheduled_at=scheduled_at,
            duration_mins=duration_mins,
            capacity=capacity,
            room=room,
            intensity=intensity,
            goal_tags=goal_tags or []
        )
        
        self.db.add(gym_class)
        self.db.commit()
        self.db.refresh(gym_class)
        
        logger.info(f"Created class: {name} at {scheduled_at}")
        return gym_class
    
    def get_class(self, class_id: UUID) -> Optional[Class]:
        """Get a class by ID."""
        return self.db.query(Class).filter(Class.id == class_id).first()
    
    def get_upcoming_classes(
        self,
        days: int = 7,
        class_type: str = None,
        goal: str = None
    ) -> List[Class]:
        """Get upcoming classes for the next X days."""
        now = datetime.utcnow()
        end = now + timedelta(days=days)
        
        query = self.db.query(Class).filter(
            and_(
                Class.scheduled_at >= now,
                Class.scheduled_at <= end,
                Class.is_cancelled == False
            )
        )
        
        if class_type:
            query = query.filter(Class.class_type == class_type)
        
        if goal:
            query = query.filter(Class.goal_tags.contains([goal]))
        
        return query.order_by(Class.scheduled_at).all()
    
    def get_classes_for_date(self, target_date: date) -> List[Class]:
        """Get all classes for a specific date."""
        start = datetime.combine(target_date, datetime.min.time())
        end = datetime.combine(target_date, datetime.max.time())
        
        return self.db.query(Class).filter(
            and_(
                Class.scheduled_at >= start,
                Class.scheduled_at <= end,
                Class.is_cancelled == False
            )
        ).order_by(Class.scheduled_at).all()
    
    def cancel_class(self, class_id: UUID, reason: str = None) -> Class:
        """Cancel a class and notify all booked members."""
        gym_class = self.get_class(class_id)
        if not gym_class:
            return None
        
        gym_class.is_cancelled = True
        gym_class.cancellation_reason = reason
        
        # Update all bookings to cancelled
        self.db.query(ClassBooking).filter(
            and_(
                ClassBooking.class_id == class_id,
                ClassBooking.status == BookingStatus.BOOKED.value
            )
        ).update({"status": BookingStatus.CANCELLED.value})
        
        self.db.commit()
        logger.info(f"Cancelled class {gym_class.name}: {reason}")
        return gym_class
    
    # ========== Booking Management ==========
    
    def book_class(
        self,
        member: Member,
        class_id: UUID
    ) -> Dict[str, Any]:
        """
        Book a class for a member.
        Returns booking status and waitlist position if applicable.
        
        IMPORTANT: Implements double-booking prevention
        - Cannot book same class twice
        - Cannot book another class at same time slot
        """
        gym_class = self.get_class(class_id)
        if not gym_class:
            return {"success": False, "error": "Class not found"}
        
        if gym_class.is_cancelled:
            return {"success": False, "error": "Class has been cancelled"}
        
        if gym_class.scheduled_at < datetime.utcnow():
            return {"success": False, "error": "Class has already started"}
        
        # Check if already booked for THIS class
        existing = self.db.query(ClassBooking).filter(
            and_(
                ClassBooking.member_id == member.id,
                ClassBooking.class_id == class_id,
                ClassBooking.status.in_([BookingStatus.BOOKED.value, BookingStatus.WAITLIST.value])
            )
        ).first()
        
        if existing:
            return {
                "success": False,
                "error": "Already booked for this class",
                "booking": existing
            }
        
        # ===== DOUBLE BOOKING PREVENTION =====
        # Check if member has another class at the SAME TIME SLOT
        class_start = gym_class.scheduled_at
        class_end = class_start + timedelta(minutes=gym_class.duration_mins)
        
        conflicting_booking = self.db.query(ClassBooking).join(Class).filter(
            and_(
                ClassBooking.member_id == member.id,
                ClassBooking.status.in_([BookingStatus.BOOKED.value, BookingStatus.WAITLIST.value]),
                Class.is_cancelled == False,
                # Check for time overlap
                Class.scheduled_at < class_end,  # Other class starts before this one ends
                (Class.scheduled_at + func.make_interval(0, 0, 0, 0, 0, Class.duration_mins, 0)) > class_start  # Other class ends after this one starts
            )
        ).first()
        
        # Fallback for SQLite (doesn't have make_interval)
        if conflicting_booking is None:
            # Use Python-based check for SQLite compatibility
            member_bookings = self.db.query(ClassBooking).join(Class).filter(
                and_(
                    ClassBooking.member_id == member.id,
                    ClassBooking.status.in_([BookingStatus.BOOKED.value, BookingStatus.WAITLIST.value]),
                    Class.is_cancelled == False,
                    Class.scheduled_at.between(
                        class_start - timedelta(hours=2),  # Check within 2 hour window
                        class_end + timedelta(hours=2)
                    )
                )
            ).all()
            
            for existing_booking in member_bookings:
                other_class = existing_booking.gym_class
                other_start = other_class.scheduled_at
                other_end = other_start + timedelta(minutes=other_class.duration_mins)
                
                # Check for time overlap
                if (class_start < other_end) and (class_end > other_start):
                    conflicting_booking = existing_booking
                    break
        
        if conflicting_booking:
            other_class = conflicting_booking.gym_class
            logger.warning(f"Double booking prevented for {member.phone}: {gym_class.name} conflicts with {other_class.name}")
            return {
                "success": False,
                "error": f"You already have '{other_class.name}' booked at {other_class.scheduled_at.strftime('%I:%M %p')}. Cannot book overlapping classes.",
                "conflict": {
                    "class_name": other_class.name,
                    "time": other_class.scheduled_at.isoformat()
                }
            }
        
        # Determine status (booked or waitlist)
        if gym_class.booked_count < gym_class.capacity:
            status = BookingStatus.BOOKED.value
            gym_class.booked_count += 1
            waitlist_position = None
        else:
            status = BookingStatus.WAITLIST.value
            gym_class.waitlist_count += 1
            waitlist_position = gym_class.waitlist_count
        
        # Create booking
        booking = ClassBooking(
            member_id=member.id,
            class_id=class_id,
            status=status,
            waitlist_position=waitlist_position
        )
        
        self.db.add(booking)
        self.db.commit()
        self.db.refresh(booking)
        
        logger.success(f"✅ Booked {member.phone} for {gym_class.name} - Status: {status}")
        
        return {
            "success": True,
            "status": status,
            "waitlist_position": waitlist_position,
            "booking": booking,
            "class": gym_class
        }
    
    def cancel_booking(
        self,
        member: Member,
        booking_id: UUID = None,
        class_id: UUID = None
    ) -> Dict[str, Any]:
        """Cancel a booking for a member."""
        query = self.db.query(ClassBooking).filter(ClassBooking.member_id == member.id)
        
        if booking_id:
            query = query.filter(ClassBooking.id == booking_id)
        elif class_id:
            query = query.filter(ClassBooking.class_id == class_id)
        else:
            return {"success": False, "error": "Provide booking_id or class_id"}
        
        booking = query.filter(
            ClassBooking.status.in_([BookingStatus.BOOKED.value, BookingStatus.WAITLIST.value])
        ).first()
        
        if not booking:
            return {"success": False, "error": "Booking not found"}
        
        gym_class = self.get_class(booking.class_id)
        
        # Check cancellation window (4 hours before)
        hours_until = (gym_class.scheduled_at - datetime.utcnow()).total_seconds() / 3600
        if hours_until < 4:
            return {"success": False, "error": "Cannot cancel within 4 hours of class"}
        
        # Update counts
        if booking.status == BookingStatus.BOOKED.value:
            gym_class.booked_count = max(0, gym_class.booked_count - 1)
            # Promote from waitlist
            self._promote_from_waitlist(gym_class)
        else:
            gym_class.waitlist_count = max(0, gym_class.waitlist_count - 1)
        
        # Cancel booking
        booking.cancel()
        
        self.db.commit()
        
        logger.info(f"Cancelled booking for {member.phone} - {gym_class.name}")
        return {"success": True, "class": gym_class}
    
    def _promote_from_waitlist(self, gym_class: Class):
        """Promote first person from waitlist to booked."""
        if gym_class.waitlist_count == 0:
            return None
        
        # Get first in waitlist
        waitlist = self.db.query(ClassBooking).filter(
            and_(
                ClassBooking.class_id == gym_class.id,
                ClassBooking.status == BookingStatus.WAITLIST.value
            )
        ).order_by(ClassBooking.waitlist_position).first()
        
        if waitlist:
            waitlist.status = BookingStatus.BOOKED.value
            waitlist.waitlist_position = None
            gym_class.booked_count += 1
            gym_class.waitlist_count -= 1
            self.db.commit()
            
            logger.info(f"Promoted member from waitlist for {gym_class.name}")
            return waitlist
        
        return None
    
    def get_member_bookings(
        self,
        member: Member,
        upcoming_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Get all bookings for a member."""
        # Optimization: Use contains_eager to populate gym_class using the existing join (avoids N+1)
        query = self.db.query(ClassBooking).join(Class).options(contains_eager(ClassBooking.gym_class)).filter(
            ClassBooking.member_id == member.id
        )
        
        if upcoming_only:
            query = query.filter(
                and_(
                    Class.scheduled_at >= datetime.utcnow(),
                    ClassBooking.status.in_([BookingStatus.BOOKED.value, BookingStatus.WAITLIST.value])
                )
            )
        
        bookings = query.order_by(Class.scheduled_at).all()
        
        return [
            {
                "booking_id": str(b.id),
                "class_id": str(b.class_id),
                "class_name": b.gym_class.name,
                "class_type": b.gym_class.class_type,
                "trainer": b.gym_class.trainer_name,
                "scheduled_at": b.gym_class.scheduled_at.isoformat(),
                "room": b.gym_class.room,
                "status": b.status,
                "waitlist_position": b.waitlist_position
            }
            for b in bookings
        ]
    
    def mark_attendance(self, booking_id: UUID, attended: bool = True):
        """Mark booking as attended or no-show."""
        booking = self.db.query(ClassBooking).filter(ClassBooking.id == booking_id).first()
        if not booking:
            return None
        
        if attended:
            booking.mark_attended()
        else:
            booking.mark_no_show()
        
        self.db.commit()
        return booking
    
    # ========== WhatsApp Formatting ==========
    
    def format_classes_for_whatsapp(self, classes: List[Class], date_str: str = None) -> str:
        """Format class list for WhatsApp message."""
        if not classes:
            return f"No classes scheduled{' for ' + date_str if date_str else ' for the coming days'}."
        
        lines = [f"🗓️ *Classes{' on ' + date_str if date_str else ' Coming Up'}*", ""]
        
        current_date = None
        for c in classes:
            class_date = c.scheduled_at.date()
            if class_date != current_date:
                current_date = class_date
                lines.append(f"📅 *{class_date.strftime('%A, %b %d')}*")
            
            time_str = c.scheduled_at.strftime("%I:%M %p").lstrip("0")
            slots = c.available_slots
            slots_text = f"✅ {slots} spots" if slots > 0 else "🔴 Waitlist"
            
            lines.append(f"  {time_str} - *{c.name}*")
            lines.append(f"    👤 {c.trainer_name} | {c.duration_mins}min | {slots_text}")
            lines.append("")
        
        lines.append("Reply with class name or time to book!")
        return "\n".join(lines)
    
    def format_booking_confirmation(self, result: Dict) -> str:
        """Format booking confirmation for WhatsApp."""
        if not result["success"]:
            return f"❌ Couldn't book: {result['error']}"
        
        gym_class = result["class"]
        status = result["status"]
        
        if status == BookingStatus.BOOKED.value:
            lines = [
                "✅ *Booking Confirmed!*",
                "",
                f"📍 *{gym_class.name}*",
                f"📅 {gym_class.scheduled_at.strftime('%A, %B %d')}",
                f"⏰ {gym_class.scheduled_at.strftime('%I:%M %p').lstrip('0')}",
                f"👤 Trainer: {gym_class.trainer_name}",
                f"🏠 Room: {gym_class.room or 'Main Floor'}",
                "",
                "I'll remind you the night before and morning of!",
                "",
                "Reply *cancel* to cancel this booking."
            ]
        else:
            position = result["waitlist_position"]
            lines = [
                "⏳ *Added to Waitlist*",
                "",
                f"📍 *{gym_class.name}*",
                f"📅 {gym_class.scheduled_at.strftime('%A, %B %d')}",
                f"⏰ {gym_class.scheduled_at.strftime('%I:%M %p').lstrip('0')}",
                "",
                f"You're #{position} on the waitlist.",
                "I'll notify you if a spot opens up!",
                "",
                "Reply *cancel* to leave the waitlist."
            ]
        
        return "\n".join(lines)
    
    def format_member_bookings(self, bookings: List[Dict]) -> str:
        """Format member's upcoming bookings."""
        if not bookings:
            return "You don't have any upcoming class bookings.\n\nSend *classes* to see the schedule!"
        
        lines = ["📅 *Your Upcoming Bookings*", ""]
        
        for b in bookings[:5]:  # Show max 5
            dt = datetime.fromisoformat(b["scheduled_at"])
            time_str = dt.strftime("%a, %b %d at %I:%M %p").lstrip("0")
            status_emoji = "✅" if b["status"] == "booked" else "⏳"
            
            lines.append(f"{status_emoji} *{b['class_name']}*")
            lines.append(f"   {time_str}")
            lines.append(f"   👤 {b['trainer']}")
            lines.append("")
        
        if len(bookings) > 5:
            lines.append(f"... and {len(bookings) - 5} more")
        
        lines.append("Reply with class name to cancel a booking.")
        return "\n".join(lines)
    
    # ========== Analytics ==========
    
    def get_utilization_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get class utilization statistics."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        classes = self.db.query(Class).filter(
            and_(
                Class.scheduled_at >= cutoff,
                Class.scheduled_at < datetime.utcnow(),
                Class.is_cancelled == False
            )
        ).all()
        
        if not classes:
            return {"total_classes": 0, "avg_utilization": 0}
        
        total_capacity = sum(c.capacity for c in classes)
        total_booked = sum(c.booked_count for c in classes)
        
        # By class type
        by_type = {}
        for c in classes:
            if c.class_type not in by_type:
                by_type[c.class_type] = {"capacity": 0, "booked": 0}
            by_type[c.class_type]["capacity"] += c.capacity
            by_type[c.class_type]["booked"] += c.booked_count
        
        for ct in by_type:
            by_type[ct]["utilization"] = round(
                (by_type[ct]["booked"] / by_type[ct]["capacity"]) * 100, 1
            ) if by_type[ct]["capacity"] > 0 else 0
        
        return {
            "total_classes": len(classes),
            "total_capacity": total_capacity,
            "total_booked": total_booked,
            "avg_utilization": round((total_booked / total_capacity) * 100, 1) if total_capacity > 0 else 0,
            "by_type": by_type
        }
