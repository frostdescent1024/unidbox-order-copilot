"""
WhatsApp Client Module for UnidBox Order Copilot

This module provides a client for the WhatsApp Business API (Cloud API)
to send messages, templates, and interactive messages to dealers.
"""

import os
import json
import httpx
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class MessageType(Enum):
    """Types of WhatsApp messages"""
    TEXT = "text"
    TEMPLATE = "template"
    INTERACTIVE = "interactive"
    IMAGE = "image"
    DOCUMENT = "document"


@dataclass
class WhatsAppConfig:
    """Configuration for WhatsApp Business API"""
    phone_number_id: str
    access_token: str
    api_version: str = "v18.0"
    base_url: str = "https://graph.facebook.com"
    
    @property
    def api_url(self) -> str:
        return f"{self.base_url}/{self.api_version}/{self.phone_number_id}/messages"


@dataclass
class MessageResult:
    """Result of sending a WhatsApp message"""
    success: bool
    message_id: Optional[str]
    recipient: str
    error: Optional[str] = None
    raw_response: Optional[Dict] = None


class WhatsAppClient:
    """
    Client for WhatsApp Business Cloud API.
    
    This client handles sending various types of messages to dealers
    including text, templates, and interactive messages.
    """
    
    def __init__(
        self,
        phone_number_id: Optional[str] = None,
        access_token: Optional[str] = None,
        config: Optional[WhatsAppConfig] = None
    ):
        """
        Initialize the WhatsApp client.
        
        Args:
            phone_number_id: WhatsApp Business phone number ID
            access_token: Meta/Facebook access token
            config: Optional WhatsAppConfig object
        """
        if config:
            self.config = config
        else:
            self.config = WhatsAppConfig(
                phone_number_id=phone_number_id or os.getenv('WHATSAPP_PHONE_NUMBER_ID', ''),
                access_token=access_token or os.getenv('WHATSAPP_ACCESS_TOKEN', '')
            )
        
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers={
                    "Authorization": f"Bearer {self.config.access_token}",
                    "Content-Type": "application/json"
                },
                timeout=30.0
            )
        return self._client
    
    async def close(self):
        """Close the HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def send_text(
        self,
        to: str,
        message: str,
        preview_url: bool = False
    ) -> MessageResult:
        """
        Send a text message.
        
        Args:
            to: Recipient phone number (with country code, no +)
            message: Text message content
            preview_url: Whether to show URL previews
            
        Returns:
            MessageResult with send status
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {
                "preview_url": preview_url,
                "body": message
            }
        }
        
        return await self._send_message(to, payload)
    
    async def send_template(
        self,
        to: str,
        template_name: str,
        language_code: str = "en",
        components: Optional[List[Dict]] = None
    ) -> MessageResult:
        """
        Send a template message.
        
        Args:
            to: Recipient phone number
            template_name: Name of the approved template
            language_code: Language code (e.g., "en", "zh_CN")
            components: Template components (header, body, buttons)
            
        Returns:
            MessageResult with send status
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
        
        return await self._send_message(to, payload)
    
    async def send_order_confirmation(
        self,
        to: str,
        order_id: str,
        items: List[Dict],
        total: float,
        delivery_date: Optional[str] = None
    ) -> MessageResult:
        """
        Send an order confirmation message.
        
        Args:
            to: Recipient phone number
            order_id: Order ID
            items: List of order items
            total: Order total
            delivery_date: Expected delivery date
            
        Returns:
            MessageResult with send status
        """
        # Build order summary
        items_text = "\n".join([
            f"• {item['name']} x{item['quantity']} - ${item['price']:.2f}"
            for item in items
        ])
        
        message = f"""✅ *Order Confirmed*

Order ID: {order_id}

*Items:*
{items_text}

*Total: ${total:.2f} SGD*
"""
        
        if delivery_date:
            message += f"\n📦 Expected Delivery: {delivery_date}"
        
        message += "\n\nThank you for your order! We'll notify you when it ships."
        
        return await self.send_text(to, message)
    
    async def send_interactive_buttons(
        self,
        to: str,
        body_text: str,
        buttons: List[Dict[str, str]],
        header_text: Optional[str] = None,
        footer_text: Optional[str] = None
    ) -> MessageResult:
        """
        Send an interactive message with buttons.
        
        Args:
            to: Recipient phone number
            body_text: Main message body
            buttons: List of buttons with 'id' and 'title' keys
            header_text: Optional header text
            footer_text: Optional footer text
            
        Returns:
            MessageResult with send status
        """
        interactive = {
            "type": "button",
            "body": {"text": body_text},
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": btn["id"],
                            "title": btn["title"][:20]  # Max 20 chars
                        }
                    }
                    for btn in buttons[:3]  # Max 3 buttons
                ]
            }
        }
        
        if header_text:
            interactive["header"] = {"type": "text", "text": header_text}
        
        if footer_text:
            interactive["footer"] = {"text": footer_text}
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "interactive",
            "interactive": interactive
        }
        
        return await self._send_message(to, payload)
    
    async def send_interactive_list(
        self,
        to: str,
        body_text: str,
        button_text: str,
        sections: List[Dict],
        header_text: Optional[str] = None,
        footer_text: Optional[str] = None
    ) -> MessageResult:
        """
        Send an interactive list message.
        
        Args:
            to: Recipient phone number
            body_text: Main message body
            button_text: Text for the list button
            sections: List of sections with items
            header_text: Optional header text
            footer_text: Optional footer text
            
        Returns:
            MessageResult with send status
        """
        interactive = {
            "type": "list",
            "body": {"text": body_text},
            "action": {
                "button": button_text[:20],
                "sections": sections
            }
        }
        
        if header_text:
            interactive["header"] = {"type": "text", "text": header_text}
        
        if footer_text:
            interactive["footer"] = {"text": footer_text}
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "interactive",
            "interactive": interactive
        }
        
        return await self._send_message(to, payload)
    
    async def send_product_options(
        self,
        to: str,
        products: List[Dict],
        intro_text: str = "Here are the products matching your request:"
    ) -> MessageResult:
        """
        Send product options as an interactive list.
        
        Args:
            to: Recipient phone number
            products: List of product dictionaries
            intro_text: Introduction text
            
        Returns:
            MessageResult with send status
        """
        sections = [{
            "title": "Available Products",
            "rows": [
                {
                    "id": f"product_{p['product_id']}",
                    "title": p['name'][:24],  # Max 24 chars
                    "description": f"${p['price']:.2f} SGD"[:72]  # Max 72 chars
                }
                for p in products[:10]  # Max 10 items
            ]
        }]
        
        return await self.send_interactive_list(
            to=to,
            body_text=intro_text,
            button_text="View Products",
            sections=sections,
            header_text="UnidBox Hardware",
            footer_text="Select a product to add to your order"
        )
    
    async def send_document(
        self,
        to: str,
        document_url: str,
        filename: str,
        caption: Optional[str] = None
    ) -> MessageResult:
        """
        Send a document (e.g., Delivery Order PDF).
        
        Args:
            to: Recipient phone number
            document_url: URL of the document
            filename: Filename to display
            caption: Optional caption
            
        Returns:
            MessageResult with send status
        """
        document = {
            "link": document_url,
            "filename": filename
        }
        
        if caption:
            document["caption"] = caption
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "document",
            "document": document
        }
        
        return await self._send_message(to, payload)
    
    async def _send_message(self, to: str, payload: Dict) -> MessageResult:
        """Send a message using the WhatsApp API"""
        if not self.config.phone_number_id or not self.config.access_token:
            return MessageResult(
                success=False,
                message_id=None,
                recipient=to,
                error="WhatsApp API not configured. Set WHATSAPP_PHONE_NUMBER_ID and WHATSAPP_ACCESS_TOKEN."
            )
        
        try:
            client = await self._get_client()
            response = await client.post(self.config.api_url, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                message_id = data.get('messages', [{}])[0].get('id')
                return MessageResult(
                    success=True,
                    message_id=message_id,
                    recipient=to,
                    raw_response=data
                )
            else:
                error_data = response.json()
                error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                return MessageResult(
                    success=False,
                    message_id=None,
                    recipient=to,
                    error=f"API Error: {error_msg}",
                    raw_response=error_data
                )
        
        except Exception as e:
            return MessageResult(
                success=False,
                message_id=None,
                recipient=to,
                error=str(e)
            )
    
    def format_phone_number(self, phone: str) -> str:
        """
        Format a phone number for WhatsApp API.
        
        Removes spaces, dashes, and leading + sign.
        Adds Singapore country code if not present.
        """
        # Remove common formatting characters
        cleaned = ''.join(c for c in phone if c.isdigit())
        
        # Add Singapore country code if not present
        if len(cleaned) == 8:  # Singapore local number
            cleaned = '65' + cleaned
        
        return cleaned
