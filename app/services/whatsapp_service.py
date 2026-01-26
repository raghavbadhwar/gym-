"""
WhatsApp Service - Handle all WhatsApp Business API interactions
"""
import httpx
from loguru import logger
from typing import Optional, List, Dict, Any

from app.config import settings


class WhatsAppService:
    """
    Service for sending and receiving WhatsApp messages
    via Meta Cloud API.
    """
    
    def __init__(self):
        self.api_url = settings.whatsapp_api_url
        self.phone_number_id = settings.whatsapp_phone_number_id
        self.access_token = settings.whatsapp_access_token
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    @property
    def messages_url(self) -> str:
        return f"{self.api_url}/{self.phone_number_id}/messages"
    
    async def send_text(self, to: str, text: str) -> dict:
        """
        Send a simple text message.
        
        Args:
            to: Recipient phone number (with country code, no +)
            text: Message text
        
        Returns:
            API response
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"body": text}
        }
        return await self._send(payload)
    
    async def send_buttons(
        self,
        to: str,
        body: str,
        buttons: List[Dict[str, str]],
        header: Optional[str] = None,
        footer: Optional[str] = None
    ) -> dict:
        """
        Send an interactive message with buttons.
        Max 3 buttons.
        
        Args:
            to: Recipient phone number
            body: Message body text
            buttons: List of {"id": "btn_id", "title": "Button Text"}
            header: Optional header text
            footer: Optional footer text
        
        Returns:
            API response
        """
        interactive = {
            "type": "button",
            "body": {"text": body},
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {"id": btn["id"], "title": btn["title"][:20]}  # Max 20 chars
                    }
                    for btn in buttons[:3]  # Max 3 buttons
                ]
            }
        }
        
        if header:
            interactive["header"] = {"type": "text", "text": header}
        if footer:
            interactive["footer"] = {"text": footer}
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "interactive",
            "interactive": interactive
        }
        return await self._send(payload)
    
    async def send_list(
        self,
        to: str,
        body: str,
        button_text: str,
        sections: List[Dict],
        header: Optional[str] = None,
        footer: Optional[str] = None
    ) -> dict:
        """
        Send an interactive list message.
        
        Args:
            to: Recipient phone number
            body: Message body text
            button_text: Text on the list button
            sections: List of sections with rows
                [
                    {
                        "title": "Section 1",
                        "rows": [
                            {"id": "row_1", "title": "Row 1", "description": "..."}
                        ]
                    }
                ]
            header: Optional header
            footer: Optional footer
        
        Returns:
            API response
        """
        interactive = {
            "type": "list",
            "body": {"text": body},
            "action": {
                "button": button_text[:20],
                "sections": sections
            }
        }
        
        if header:
            interactive["header"] = {"type": "text", "text": header}
        if footer:
            interactive["footer"] = {"text": footer}
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "interactive",
            "interactive": interactive
        }
        return await self._send(payload)
    
    async def send_template(
        self,
        to: str,
        template_name: str,
        language_code: str = "en",
        components: Optional[List[Dict]] = None
    ) -> dict:
        """
        Send a pre-approved template message.
        
        Args:
            to: Recipient phone number
            template_name: Name of approved template
            language_code: Language code (default: en)
            components: Template components (header, body, button params)
        
        Returns:
            API response
        """
        template = {
            "name": template_name,
            "language": {"code": language_code}
        }
        
        if components:
            template["components"] = components
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "template",
            "template": template
        }
        return await self._send(payload)
    
    async def send_image(
        self,
        to: str,
        image_url: str,
        caption: Optional[str] = None
    ) -> dict:
        """
        Send an image message.
        
        Args:
            to: Recipient phone number
            image_url: Public URL of the image
            caption: Optional caption text
        
        Returns:
            API response
        """
        image = {"link": image_url}
        if caption:
            image["caption"] = caption
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "image",
            "image": image
        }
        return await self._send(payload)
    
    async def send_video(
        self,
        to: str,
        video_url: str,
        caption: Optional[str] = None
    ) -> dict:
        """
        Send a video message (for tutorials).
        
        Args:
            to: Recipient phone number
            video_url: Public URL of the video (max 16MB)
            caption: Optional caption text
        
        Returns:
            API response
        """
        video = {"link": video_url}
        if caption:
            video["caption"] = caption
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "video",
            "video": video
        }
        return await self._send(payload)
    
    async def mark_as_read(self, message_id: str) -> dict:
        """
        Mark a message as read (shows blue ticks).
        
        Args:
            message_id: WhatsApp message ID
        """
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }
        return await self._send(payload)
    
    async def _send(self, payload: dict) -> dict:
        """
        Internal method to send API request.
        """
        try:
            # Configure timeout to prevent hanging on network issues
            timeout = httpx.Timeout(30.0, connect=10.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    self.messages_url,
                    json=payload,
                    headers=self.headers
                )
                response.raise_for_status()
                result = response.json()
                logger.info(f"Message sent successfully: {result}")
                return result
        except httpx.TimeoutException as e:
            logger.error(f"WhatsApp API timeout: {e}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"WhatsApp API error: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {e}")
            raise
    
    def parse_webhook_message(self, data: dict) -> Optional[Dict[str, Any]]:
        """
        Parse incoming webhook data into a simplified message dict.
        
        Returns:
            {
                "from": "919876543210",
                "name": "John Doe",
                "type": "text|button|list|...",
                "content": "message text or button id",
                "message_id": "wamid.xxx",
                "timestamp": "1234567890"
            }
        """
        try:
            entry = data.get("entry", [])
            if not entry:
                return None
            
            changes = entry[0].get("changes", [])
            if not changes:
                return None
            
            value = changes[0].get("value", {})
            messages = value.get("messages", [])
            
            if not messages:
                return None
            
            msg = messages[0]
            contacts = value.get("contacts", [{}])
            contact_name = contacts[0].get("profile", {}).get("name", "Unknown")
            
            result = {
                "from": msg.get("from"),
                "name": contact_name,
                "message_id": msg.get("id"),
                "timestamp": msg.get("timestamp"),
                "type": msg.get("type")
            }
            
            # Parse content based on type
            msg_type = msg.get("type")
            
            if msg_type == "text":
                result["content"] = msg.get("text", {}).get("body", "")
            
            elif msg_type == "interactive":
                interactive = msg.get("interactive", {})
                int_type = interactive.get("type")
                
                if int_type == "button_reply":
                    result["content"] = interactive.get("button_reply", {}).get("id", "")
                    result["button_text"] = interactive.get("button_reply", {}).get("title", "")
                elif int_type == "list_reply":
                    result["content"] = interactive.get("list_reply", {}).get("id", "")
                    result["list_title"] = interactive.get("list_reply", {}).get("title", "")
            
            elif msg_type == "image":
                result["content"] = "[IMAGE]"
                result["media_id"] = msg.get("image", {}).get("id")
            
            elif msg_type == "video":
                result["content"] = "[VIDEO]"
                result["media_id"] = msg.get("video", {}).get("id")
            
            else:
                result["content"] = f"[{msg_type.upper()}]"
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing webhook: {e}")
            return None


# Singleton instance
whatsapp_service = WhatsAppService()
