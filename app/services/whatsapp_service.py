"""
WhatsApp Service - Handle all WhatsApp Business API interactions
"""
import httpx
from loguru import logger
from typing import Optional, List, Dict, Any
import asyncio

from app.config import settings

# WhatsApp message limits
WHATSAPP_MAX_MESSAGE_LENGTH = 4096
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds


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
    
    def _validate_and_split_message(self, text: str) -> List[str]:
        """
        Validate message length and split if necessary.
        WhatsApp has a 4,096 character limit per message.
        
        Args:
            text: Message text to validate and potentially split
            
        Returns:
            List of message chunks (single item if within limit)
        """
        if len(text) <= WHATSAPP_MAX_MESSAGE_LENGTH:
            return [text]
        
        logger.warning(f"Message length {len(text)} exceeds WhatsApp limit of {WHATSAPP_MAX_MESSAGE_LENGTH}")
        
        # Split long message into chunks
        chunks = []
        margin = 100  # Leave margin for continuation markers
        max_chunk_size = WHATSAPP_MAX_MESSAGE_LENGTH - margin
        
        # Try to split by lines first
        lines = text.split('\n')
        current_chunk = ""
        
        for line in lines:
            # If a single line is still too long even for one chunk, force split
            if len(line) > max_chunk_size:
                # Save current chunk first
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                
                # Force split long line by character chunks
                while len(line) > max_chunk_size:
                    chunks.append(line[:max_chunk_size])
                    line = line[max_chunk_size:]
                
                # Add remainder if any
                if line:
                    current_chunk = line + "\n"
            # Normal line processing
            elif len(current_chunk) + len(line) + 1 > max_chunk_size:
                # Save current chunk
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = line + "\n"
            else:
                current_chunk += line + "\n"
        
        # Add remaining content
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        # Add continuation markers
        if len(chunks) > 1:
            for i in range(len(chunks)):
                if i < len(chunks) - 1:
                    chunks[i] += f"\n\n_(...{i+1}/{len(chunks)})_"
                else:
                    chunks[i] = f"_(...{i+1}/{len(chunks)})_\n\n" + chunks[i]
        
        logger.info(f"Message split into {len(chunks)} chunk(s)")
        return chunks
    
    async def send_text(self, to: str, text: str) -> dict:
        """
        Send a simple text message with automatic splitting if too long.
        
        Args:
            to: Recipient phone number (with country code, no +)
            text: Message text
        
        Returns:
            API response (last chunk if multiple sent)
        """
        # Validate and split if necessary
        chunks = self._validate_and_split_message(text)
        
        result = None
        for i, chunk in enumerate(chunks):
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to,
                "type": "text",
                "text": {"body": chunk}
            }
            result = await self._send(payload)
            
            # Add small delay between chunks to ensure order
            if i < len(chunks) - 1:
                await asyncio.sleep(0.5)
        
        return result
    
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
        Internal method to send API request with retry logic.
        Implements exponential backoff for transient failures.
        """
        last_exception = None
        
        for attempt in range(MAX_RETRIES):
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
                last_exception = e
                logger.warning(f"WhatsApp API timeout (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAY * (2 ** attempt)  # Exponential backoff
                    logger.info(f"Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                continue
                
            except httpx.HTTPStatusError as e:
                # Don't retry on client errors (4xx), but do retry on server errors (5xx)
                if 400 <= e.response.status_code < 500:
                    logger.error(f"WhatsApp API client error: {e.response.text}")
                    raise  # Don't retry client errors
                else:
                    last_exception = e
                    logger.warning(f"WhatsApp API server error (attempt {attempt + 1}/{MAX_RETRIES}): {e.response.text}")
                    if attempt < MAX_RETRIES - 1:
                        delay = RETRY_DELAY * (2 ** attempt)
                        logger.info(f"Retrying in {delay}s...")
                        await asyncio.sleep(delay)
                    continue
                    
            except Exception as e:
                last_exception = e
                logger.error(f"Unexpected error sending WhatsApp message (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAY * (2 ** attempt)
                    await asyncio.sleep(delay)
                continue
        
        # All retries exhausted
        logger.error(f"Failed to send WhatsApp message after {MAX_RETRIES} attempts")
        raise last_exception
    
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
