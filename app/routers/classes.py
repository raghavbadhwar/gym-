"""
Classes Router - API endpoints for class management and booking
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, date
from uuid import UUID

from app.database import get_db
from app.auth import get_admin_api_key
from app.services.member_service import MemberService
from app.services.booking_service import BookingService

router = APIRouter(
    prefix="/api/v1/classes",
    tags=["Classes"],
    dependencies=[Depends(get_admin_api_key)]
)


# ========== Pydantic Models ==========

class ClassCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    class_type: str = Field(..., description="yoga, hiit, spin, strength, dance, etc.")
    trainer_name: str
    scheduled_at: datetime
    duration_mins: int = 45
    capacity: int = 20
    room: Optional[str] = None
    intensity: str = "medium"
    goal_tags: Optional[List[str]] = []


class BookingCreate(BaseModel):
    member_phone: str
    class_id: str


class BookingCancel(BaseModel):
    member_phone: str


# ========== Endpoints ==========

@router.post("/", status_code=201)
def create_class(class_data: ClassCreate, db: Session = Depends(get_db)):
    """Create a new gym class."""
    service = BookingService(db)
    
    gym_class = service.create_class(**class_data.model_dump())
    
    return {
        "message": "Class created",
        "id": str(gym_class.id),
        "name": gym_class.name,
        "scheduled_at": gym_class.scheduled_at.isoformat()
    }


@router.get("/")
def list_classes(
    date_str: Optional[str] = Query(None, alias="date", description="Date in YYYY-MM-DD format"),
    days: int = Query(7, description="Number of days to fetch (if no date specified)"),
    class_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List upcoming classes."""
    service = BookingService(db)
    
    if date_str:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        classes = service.get_classes_for_date(target_date)
        formatted = service.format_classes_for_whatsapp(classes, date_str)
    else:
        classes = service.get_upcoming_classes(days=days, class_type=class_type)
        formatted = service.format_classes_for_whatsapp(classes)
    
    return {
        "count": len(classes),
        "classes": [
            {
                "id": str(c.id),
                "name": c.name,
                "class_type": c.class_type,
                "trainer": c.trainer_name,
                "scheduled_at": c.scheduled_at.isoformat(),
                "duration_mins": c.duration_mins,
                "room": c.room,
                "capacity": c.capacity,
                "booked": c.booked_count,
                "available": c.available_slots,
                "waitlist": c.waitlist_count,
                "intensity": c.intensity,
                "goal_tags": c.goal_tags or []
            }
            for c in classes
        ],
        "formatted": formatted
    }


@router.get("/{class_id}")
def get_class(class_id: str, db: Session = Depends(get_db)):
    """Get class details."""
    service = BookingService(db)
    
    gym_class = service.get_class(UUID(class_id))
    if not gym_class:
        raise HTTPException(status_code=404, detail="Class not found")
    
    return {
        "id": str(gym_class.id),
        "name": gym_class.name,
        "class_type": gym_class.class_type,
        "trainer": gym_class.trainer_name,
        "scheduled_at": gym_class.scheduled_at.isoformat(),
        "duration_mins": gym_class.duration_mins,
        "room": gym_class.room,
        "capacity": gym_class.capacity,
        "booked": gym_class.booked_count,
        "available": gym_class.available_slots,
        "waitlist": gym_class.waitlist_count,
        "is_full": gym_class.is_full,
        "can_book": gym_class.can_book(),
        "intensity": gym_class.intensity,
        "goal_tags": gym_class.goal_tags or []
    }


@router.delete("/{class_id}")
def cancel_class(class_id: str, reason: Optional[str] = None, db: Session = Depends(get_db)):
    """Cancel a class."""
    service = BookingService(db)
    
    gym_class = service.cancel_class(UUID(class_id), reason=reason)
    if not gym_class:
        raise HTTPException(status_code=404, detail="Class not found")
    
    return {"message": "Class cancelled", "id": str(gym_class.id)}


# ========== Bookings ==========

@router.post("/book")
def book_class(booking: BookingCreate, db: Session = Depends(get_db)):
    """Book a class for a member."""
    member_service = MemberService(db)
    booking_service = BookingService(db)
    
    member = member_service.get_by_phone(booking.member_phone)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    result = booking_service.book_class(member, UUID(booking.class_id))
    
    return {
        "success": result["success"],
        "status": result.get("status"),
        "waitlist_position": result.get("waitlist_position"),
        "message": booking_service.format_booking_confirmation(result),
        "error": result.get("error")
    }


@router.delete("/{class_id}/cancel")
def cancel_booking(class_id: str, data: BookingCancel, db: Session = Depends(get_db)):
    """Cancel a member's booking."""
    member_service = MemberService(db)
    booking_service = BookingService(db)
    
    member = member_service.get_by_phone(data.member_phone)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    result = booking_service.cancel_booking(member, class_id=UUID(class_id))
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return {"message": "Booking cancelled", "success": True}


@router.get("/member/{phone}/bookings")
def get_member_bookings(phone: str, db: Session = Depends(get_db)):
    """Get all bookings for a member."""
    member_service = MemberService(db)
    booking_service = BookingService(db)
    
    member = member_service.get_by_phone(phone)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    bookings = booking_service.get_member_bookings(member)
    formatted = booking_service.format_member_bookings(bookings)
    
    return {
        "count": len(bookings),
        "bookings": bookings,
        "formatted": formatted
    }


@router.post("/{class_id}/attendance/{booking_id}")
def mark_attendance(
    class_id: str,
    booking_id: str,
    attended: bool = True,
    db: Session = Depends(get_db)
):
    """Mark booking as attended or no-show."""
    service = BookingService(db)
    
    booking = service.mark_attendance(UUID(booking_id), attended=attended)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    return {
        "message": f"Marked as {'attended' if attended else 'no-show'}",
        "booking_id": str(booking.id)
    }


@router.get("/stats/utilization")
def get_utilization_stats(days: int = 7, db: Session = Depends(get_db)):
    """Get class utilization statistics."""
    service = BookingService(db)
    return service.get_utilization_stats(days=days)
