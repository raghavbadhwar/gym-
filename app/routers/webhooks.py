"""
Webhooks Router - WhatsApp webhook handling with full workflow support

This module handles:
- Webhook verification (GET) for Meta
- Message receiving (POST) with media handling
- Intent classification and routing
- Escalation and error handling

Uses Loguru for detailed logging as specified.
"""
from fastapi import APIRouter, Request, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from loguru import logger
from typing import Optional

from app.config import settings
from app.database import get_db
from app.services.whatsapp_service import whatsapp_service
from app.services.ai_engine import ai_engine, Intent
from app.services.member_service import MemberService
from app.services.security import validate_whatsapp_signature
from app.flows.handlers import MessageHandler

router = APIRouter(prefix="/api/v1/webhooks", tags=["Webhooks"])


@router.get("/whatsapp")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge")
):
    """
    WhatsApp webhook verification endpoint.
    Meta sends a GET request to verify the callback URL.
    
    This is the critical first step for WhatsApp integration.
    """
    logger.info(f"Webhook verification request - mode: {hub_mode}")
    
    if hub_mode == "subscribe" and hub_verify_token == settings.whatsapp_verify_token:
        logger.success("WhatsApp webhook verified successfully ✅")
        return int(hub_challenge)
    
    logger.warning(f"Webhook verification failed! Token received: {hub_verify_token}")
    raise HTTPException(status_code=403, detail="Verification failed - Invalid token")


@router.post("/whatsapp", dependencies=[Depends(validate_whatsapp_signature)])
async def receive_message(request: Request, db: Session = Depends(get_db)):
    """
    WhatsApp webhook endpoint for receiving messages.
    
    Workflow:
    1. Parse incoming message
    2. Handle media (image/audio/video) with polite rejection
    3. Check for escalation triggers
    4. Classify intent
    5. Route to appropriate handler
    6. Send response
    
    Always returns 200 to prevent Meta from retrying.
    """
    try:
        data = await request.json()
        logger.debug(f"Webhook payload received: {data}")
        
        # Parse the incoming message
        message = whatsapp_service.parse_webhook_message(data)
        
        if not message:
            # Might be a status update (delivered, read, etc.)
            logger.debug("No message content - likely a status update")
            return {"status": "ok"}
        
        phone = message["from"]
        content = message.get("content", "")
        msg_type = message.get("type", "text")
        
        logger.info(f"📩 Message from {phone}: [{msg_type}] {content[:50]}...")
        
        # ===== MEDIA HANDLER =====
        # If webhook contains type=image or type=audio, reply with media message
        if msg_type in ["image", "audio", "video", "document", "sticker"]:
            logger.info(f"Media message received: {msg_type}")
            response = ai_engine.get_media_response(msg_type)
            await whatsapp_service.send_text(phone, response)
            return {"status": "ok", "handled": "media_rejection"}
        
        # Mark message as read
        if message.get("message_id"):
            try:
                await whatsapp_service.mark_as_read(message["message_id"])
            except Exception as e:
                logger.warning(f"Could not mark message as read: {e}")
        
        # ===== CHECK USER STATUS =====
        member_service = MemberService(db)
        member = member_service.get_by_phone(phone)
        is_new_user = member is None
        
        # ===== INTENT CLASSIFICATION =====
        intent_result = await ai_engine.classify_intent(content, is_new_user=is_new_user)
        intent = intent_result["intent"]
        confidence = intent_result["confidence"]
        
        logger.info(f"🧠 Intent: {intent.value} (confidence: {confidence:.2f})")
        
        # ===== ESCALATION HANDLER (Safety Valve) =====
        if intent_result.get("requires_escalation"):
            logger.warning(f"⚠️ ESCALATION triggered for {phone}: {intent_result.get('escalation_reason')}")
            
            # Mark member for escalation if exists
            if member:
                member_service.mark_for_escalation(phone, intent_result.get('escalation_reason'))
            
            # Send escalation response
            await whatsapp_service.send_text(phone, ai_engine.get_escalation_response())
            
            # Notify manager if configured
            if settings.manager_phone:
                manager_msg = f"🚨 ESCALATION NEEDED\n\nPhone: {phone}\nReason: {intent_result.get('escalation_reason')}\nMessage: {content[:200]}"
                try:
                    await whatsapp_service.send_text(settings.manager_phone, manager_msg)
                    logger.info(f"Manager notified at {settings.manager_phone}")
                except Exception as e:
                    logger.error(f"Failed to notify manager: {e}")
            
            # Store escalation in DB
            member_service.log_message(phone, content, "inbound", intent=Intent.HUMAN_HELP.value)
            
            return {"status": "ok", "handled": "escalation"}
        
        # ===== AMBIGUITY HANDLER =====
        if intent_result.get("ambiguous") and confidence < 0.5:
            logger.info(f"🤔 Ambiguous request detected (confidence: {confidence})")
            response = ai_engine.get_ambiguity_response(intent, intent_result.get("entities", {}))
            await whatsapp_service.send_text(phone, response)
            member_service.log_message(phone, content, "inbound", intent=intent.value)
            return {"status": "ok", "handled": "ambiguity_clarification"}
        
        # ===== MAIN MESSAGE PROCESSING =====
        # Process through the main message handler
        handler = MessageHandler(db)
        response = await handler.handle(message)
        
        # ===== SEND RESPONSE =====
        if response:
            await _send_response(phone, response)
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.exception(f"❌ Error processing webhook: {e}")
        # Return 200 anyway to prevent Meta from retrying
        return {"status": "error", "message": str(e)}


async def _send_response(phone: str, response):
    """Helper to send different response types."""
    if isinstance(response, str):
        await whatsapp_service.send_text(phone, response)
    elif isinstance(response, dict):
        response_type = response.get("type", "text")
        
        if response_type == "buttons":
            await whatsapp_service.send_buttons(
                to=phone,
                body=response["body"],
                buttons=response["buttons"],
                header=response.get("header"),
                footer=response.get("footer")
            )
        elif response_type == "list":
            await whatsapp_service.send_list(
                to=phone,
                body=response["body"],
                button_text=response["button_text"],
                sections=response["sections"],
                header=response.get("header"),
                footer=response.get("footer")
            )
        elif response_type == "text":
            await whatsapp_service.send_text(phone, response["text"])


@router.post("/test/send")
async def test_send_message(
    phone: str,
    message: str,
    db: Session = Depends(get_db)
):
    """
    Test endpoint to send a WhatsApp message.
    For development/testing purposes only.
    """
    if settings.app_env != "development":
        raise HTTPException(status_code=403, detail="Only available in development mode")
    
    try:
        result = await whatsapp_service.send_text(phone, message)
        logger.info(f"Test message sent to {phone}")
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Test message failed: {e}")
        return {"success": False, "error": str(e)}


@router.get("/health")
async def webhook_health():
    """Health check for webhooks specifically."""
    return {
        "webhook_status": "active",
        "verify_token_set": bool(settings.whatsapp_verify_token),
        "whatsapp_configured": bool(settings.whatsapp_access_token),
        "ai_configured": bool(settings.openai_api_key or settings.gemini_api_key)
    }
