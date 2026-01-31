"""
Webhook Handler Module for UnidBox Order Copilot

This module handles incoming webhooks from the WhatsApp Business API,
validates signatures, and routes messages to the message handler.
"""

import hmac
import hashlib
import json
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass
from datetime import datetime


@dataclass
class IncomingMessage:
    """Represents an incoming WhatsApp message"""
    message_id: str
    from_number: str
    timestamp: str
    message_type: str  # text, interactive, image, document, etc.
    text: Optional[str] = None
    interactive_type: Optional[str] = None  # button_reply, list_reply
    interactive_id: Optional[str] = None
    interactive_title: Optional[str] = None
    media_id: Optional[str] = None
    media_url: Optional[str] = None
    caption: Optional[str] = None
    context_message_id: Optional[str] = None  # For replies


@dataclass
class StatusUpdate:
    """Represents a message status update"""
    message_id: str
    recipient: str
    status: str  # sent, delivered, read, failed
    timestamp: str
    error_code: Optional[str] = None
    error_message: Optional[str] = None


class WebhookHandler:
    """
    Handles incoming webhooks from WhatsApp Business API.
    
    This class validates webhook signatures, parses incoming messages,
    and routes them to the appropriate handlers.
    """
    
    def __init__(
        self,
        verify_token: Optional[str] = None,
        app_secret: Optional[str] = None
    ):
        """
        Initialize the webhook handler.
        
        Args:
            verify_token: Token for webhook verification
            app_secret: App secret for signature validation
        """
        import os
        self.verify_token = verify_token or os.getenv('WHATSAPP_VERIFY_TOKEN', 'unidbox_verify_token')
        self.app_secret = app_secret or os.getenv('WHATSAPP_APP_SECRET', '')
        
        # Callbacks
        self._on_message: Optional[Callable] = None
        self._on_status: Optional[Callable] = None
        self._on_error: Optional[Callable] = None
    
    def set_message_callback(self, callback: Callable):
        """Set callback for incoming messages"""
        self._on_message = callback
    
    def set_status_callback(self, callback: Callable):
        """Set callback for status updates"""
        self._on_status = callback
    
    def set_error_callback(self, callback: Callable):
        """Set callback for errors"""
        self._on_error = callback
    
    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """
        Verify webhook subscription from Meta.
        
        Args:
            mode: hub.mode parameter
            token: hub.verify_token parameter
            challenge: hub.challenge parameter
            
        Returns:
            Challenge string if valid, None otherwise
        """
        if mode == "subscribe" and token == self.verify_token:
            return challenge
        return None
    
    def validate_signature(self, payload: bytes, signature: str) -> bool:
        """
        Validate the X-Hub-Signature-256 header.
        
        Args:
            payload: Raw request body
            signature: X-Hub-Signature-256 header value
            
        Returns:
            True if signature is valid
        """
        if not self.app_secret:
            # Skip validation if no secret configured (development mode)
            return True
        
        if not signature or not signature.startswith("sha256="):
            return False
        
        expected_signature = hmac.new(
            self.app_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature[7:], expected_signature)
    
    async def handle_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle an incoming webhook payload.
        
        Args:
            payload: Parsed JSON payload from webhook
            
        Returns:
            Processing result dictionary
        """
        results = {
            "messages_processed": 0,
            "statuses_processed": 0,
            "errors": []
        }
        
        try:
            # Extract entries
            entries = payload.get("entry", [])
            
            for entry in entries:
                changes = entry.get("changes", [])
                
                for change in changes:
                    if change.get("field") != "messages":
                        continue
                    
                    value = change.get("value", {})
                    
                    # Process messages
                    messages = value.get("messages", [])
                    for msg in messages:
                        try:
                            incoming = self._parse_message(msg, value)
                            if incoming and self._on_message:
                                await self._on_message(incoming)
                            results["messages_processed"] += 1
                        except Exception as e:
                            results["errors"].append(str(e))
                            if self._on_error:
                                await self._on_error(e, msg)
                    
                    # Process status updates
                    statuses = value.get("statuses", [])
                    for status in statuses:
                        try:
                            update = self._parse_status(status)
                            if update and self._on_status:
                                await self._on_status(update)
                            results["statuses_processed"] += 1
                        except Exception as e:
                            results["errors"].append(str(e))
        
        except Exception as e:
            results["errors"].append(f"Webhook processing error: {str(e)}")
        
        return results
    
    def _parse_message(self, msg: Dict, value: Dict) -> Optional[IncomingMessage]:
        """Parse a message from the webhook payload"""
        message_type = msg.get("type", "text")
        
        # Get sender info
        from_number = msg.get("from", "")
        message_id = msg.get("id", "")
        timestamp = msg.get("timestamp", "")
        
        # Get context (for replies)
        context = msg.get("context", {})
        context_message_id = context.get("id")
        
        incoming = IncomingMessage(
            message_id=message_id,
            from_number=from_number,
            timestamp=timestamp,
            message_type=message_type,
            context_message_id=context_message_id
        )
        
        # Parse based on message type
        if message_type == "text":
            incoming.text = msg.get("text", {}).get("body", "")
        
        elif message_type == "interactive":
            interactive = msg.get("interactive", {})
            interactive_type = interactive.get("type", "")
            incoming.interactive_type = interactive_type
            
            if interactive_type == "button_reply":
                reply = interactive.get("button_reply", {})
                incoming.interactive_id = reply.get("id", "")
                incoming.interactive_title = reply.get("title", "")
                incoming.text = incoming.interactive_id  # Use ID as text for processing
            
            elif interactive_type == "list_reply":
                reply = interactive.get("list_reply", {})
                incoming.interactive_id = reply.get("id", "")
                incoming.interactive_title = reply.get("title", "")
                incoming.text = incoming.interactive_id
        
        elif message_type == "image":
            image = msg.get("image", {})
            incoming.media_id = image.get("id", "")
            incoming.caption = image.get("caption", "")
        
        elif message_type == "document":
            document = msg.get("document", {})
            incoming.media_id = document.get("id", "")
            incoming.caption = document.get("caption", "")
        
        elif message_type == "audio":
            audio = msg.get("audio", {})
            incoming.media_id = audio.get("id", "")
        
        elif message_type == "location":
            location = msg.get("location", {})
            lat = location.get("latitude", "")
            lon = location.get("longitude", "")
            incoming.text = f"Location: {lat}, {lon}"
        
        return incoming
    
    def _parse_status(self, status: Dict) -> StatusUpdate:
        """Parse a status update from the webhook payload"""
        return StatusUpdate(
            message_id=status.get("id", ""),
            recipient=status.get("recipient_id", ""),
            status=status.get("status", ""),
            timestamp=status.get("timestamp", ""),
            error_code=status.get("errors", [{}])[0].get("code") if status.get("errors") else None,
            error_message=status.get("errors", [{}])[0].get("message") if status.get("errors") else None
        )


# Express.js style route handlers for easy integration

def create_webhook_routes(handler: WebhookHandler):
    """
    Create route handlers for Express.js or similar frameworks.
    
    Returns a dictionary of route handlers that can be used with
    various web frameworks.
    """
    
    async def get_handler(query_params: Dict) -> tuple:
        """Handle GET request for webhook verification"""
        mode = query_params.get("hub.mode", "")
        token = query_params.get("hub.verify_token", "")
        challenge = query_params.get("hub.challenge", "")
        
        result = handler.verify_webhook(mode, token, challenge)
        if result:
            return 200, result
        return 403, "Verification failed"
    
    async def post_handler(body: bytes, headers: Dict) -> tuple:
        """Handle POST request for incoming webhooks"""
        # Validate signature
        signature = headers.get("x-hub-signature-256", "")
        if not handler.validate_signature(body, signature):
            return 401, {"error": "Invalid signature"}
        
        # Parse and handle payload
        try:
            payload = json.loads(body)
            result = await handler.handle_webhook(payload)
            return 200, result
        except json.JSONDecodeError:
            return 400, {"error": "Invalid JSON"}
        except Exception as e:
            return 500, {"error": str(e)}
    
    return {
        "get": get_handler,
        "post": post_handler
    }
