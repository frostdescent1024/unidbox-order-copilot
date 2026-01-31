"""
Message Handler Module for UnidBox Order Copilot

This module handles incoming WhatsApp messages, processes them through
the AI intent parser, and orchestrates the order flow.
"""

import json
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

# Import AI modules (relative imports for package structure)
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.intent_parser import IntentParser, ParsedIntent, IntentType
from ai.product_matcher import ProductMatcher, MatchResult
from ai.order_extractor import OrderExtractor, ExtractedOrder


class ConversationState(Enum):
    """States in the order conversation flow"""
    IDLE = "idle"
    AWAITING_INQUIRY = "awaiting_inquiry"
    PROCESSING = "processing"
    AWAITING_PRODUCT_SELECTION = "awaiting_product_selection"
    AWAITING_QUANTITY = "awaiting_quantity"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    AWAITING_DELIVERY_INFO = "awaiting_delivery_info"
    ORDER_CONFIRMED = "order_confirmed"
    COMPLETED = "completed"


@dataclass
class ConversationContext:
    """Context for an ongoing conversation with a dealer"""
    phone_number: str
    state: ConversationState
    parsed_intent: Optional[Dict] = None
    matched_products: Optional[List[Dict]] = None
    extracted_order: Optional[Dict] = None
    pending_items: Optional[List[Dict]] = None
    current_item_index: int = 0
    last_message_at: Optional[str] = None
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()


class MessageHandler:
    """
    Handles incoming WhatsApp messages and manages conversation flow.
    
    This class orchestrates the entire order flow from initial inquiry
    to order confirmation, using the AI modules for parsing and matching.
    """
    
    def __init__(
        self,
        intent_parser: Optional[IntentParser] = None,
        product_matcher: Optional[ProductMatcher] = None,
        order_extractor: Optional[OrderExtractor] = None,
        catalog_path: Optional[str] = None
    ):
        """
        Initialize the message handler.
        
        Args:
            intent_parser: IntentParser instance
            product_matcher: ProductMatcher instance
            order_extractor: OrderExtractor instance
            catalog_path: Path to product catalog JSON
        """
        self.intent_parser = intent_parser or IntentParser()
        self.product_matcher = product_matcher or ProductMatcher(catalog_path)
        self.order_extractor = order_extractor or OrderExtractor()
        
        # In-memory conversation storage (replace with database in production)
        self.conversations: Dict[str, ConversationContext] = {}
        
        # Callbacks for sending messages
        self._send_text_callback: Optional[Callable] = None
        self._send_interactive_callback: Optional[Callable] = None
        self._send_products_callback: Optional[Callable] = None
    
    def set_send_callbacks(
        self,
        send_text: Callable,
        send_interactive: Optional[Callable] = None,
        send_products: Optional[Callable] = None
    ):
        """Set callbacks for sending messages"""
        self._send_text_callback = send_text
        self._send_interactive_callback = send_interactive
        self._send_products_callback = send_products
    
    async def handle_message(
        self,
        phone_number: str,
        message_text: str,
        message_type: str = "text"
    ) -> Dict[str, Any]:
        """
        Handle an incoming WhatsApp message.
        
        Args:
            phone_number: Sender's phone number
            message_text: Message content
            message_type: Type of message (text, interactive, etc.)
            
        Returns:
            Response dictionary with action and message
        """
        # Get or create conversation context
        context = self._get_or_create_context(phone_number)
        context.last_message_at = datetime.utcnow().isoformat()
        
        # Route based on conversation state
        if context.state == ConversationState.IDLE or context.state == ConversationState.AWAITING_INQUIRY:
            return await self._handle_new_inquiry(context, message_text)
        
        elif context.state == ConversationState.AWAITING_PRODUCT_SELECTION:
            return await self._handle_product_selection(context, message_text)
        
        elif context.state == ConversationState.AWAITING_QUANTITY:
            return await self._handle_quantity_input(context, message_text)
        
        elif context.state == ConversationState.AWAITING_CONFIRMATION:
            return await self._handle_confirmation(context, message_text)
        
        elif context.state == ConversationState.AWAITING_DELIVERY_INFO:
            return await self._handle_delivery_info(context, message_text)
        
        else:
            # Default: treat as new inquiry
            return await self._handle_new_inquiry(context, message_text)
    
    async def _handle_new_inquiry(
        self,
        context: ConversationContext,
        message: str
    ) -> Dict[str, Any]:
        """Handle a new order inquiry"""
        context.state = ConversationState.PROCESSING
        
        # Parse the intent
        parsed = await self.intent_parser.parse(message)
        context.parsed_intent = self.intent_parser.to_dict(parsed)
        
        # Check intent type
        if parsed.intent_type == IntentType.UNCLEAR:
            context.state = ConversationState.AWAITING_INQUIRY
            return {
                "action": "send_text",
                "message": "Hi! I'm the UnidBox Order Copilot. I can help you with:\n\n"
                          "• Placing orders for hardware supplies\n"
                          "• Checking product prices and availability\n"
                          "• Tracking your order status\n\n"
                          "Just tell me what you need! For example:\n"
                          "_'I need 10 Acorn ceiling fans for a condo project'_"
            }
        
        if parsed.intent_type == IntentType.ORDER_STATUS:
            return {
                "action": "send_text",
                "message": "To check your order status, please provide your order number.\n\n"
                          "Example: _UB-20260131-ABC123_"
            }
        
        # Match products from the inquiry
        matched_products = []
        for product_intent in parsed.products:
            result = self.product_matcher.match(
                query=product_intent.raw_text,
                brand=product_intent.brand,
                category=product_intent.category,
                max_results=3
            )
            if result.matches:
                matched_products.extend([
                    self.product_matcher.to_dict(result)['matches'][0]
                    for _ in range(1)  # Take best match
                ])
        
        context.matched_products = matched_products
        
        # Extract order
        order = self.order_extractor.extract(
            context.parsed_intent,
            matched_products,
            message
        )
        context.extracted_order = self.order_extractor.to_dict(order)
        
        # Check if we need clarification
        if order.needs_confirmation and order.confirmation_notes:
            context.state = ConversationState.AWAITING_CONFIRMATION
            
            # Build order summary
            summary = self._build_order_summary(order)
            
            notes = "\n".join([f"⚠️ {note}" for note in order.confirmation_notes])
            
            return {
                "action": "send_interactive",
                "message": f"📋 *Order Summary*\n\n{summary}\n\n{notes}",
                "buttons": [
                    {"id": "confirm_order", "title": "Confirm Order"},
                    {"id": "modify_order", "title": "Modify Order"},
                    {"id": "cancel_order", "title": "Cancel"}
                ]
            }
        
        # If order is ready, ask for confirmation
        context.state = ConversationState.AWAITING_CONFIRMATION
        summary = self._build_order_summary(order)
        
        return {
            "action": "send_interactive",
            "message": f"📋 *Order Summary*\n\n{summary}\n\nWould you like to proceed with this order?",
            "buttons": [
                {"id": "confirm_order", "title": "Confirm Order"},
                {"id": "modify_order", "title": "Modify Order"},
                {"id": "cancel_order", "title": "Cancel"}
            ]
        }
    
    async def _handle_product_selection(
        self,
        context: ConversationContext,
        message: str
    ) -> Dict[str, Any]:
        """Handle product selection from list"""
        # Check if message is a product selection
        if message.startswith("product_"):
            product_id = message.replace("product_", "")
            # Find the product and add to order
            product = self.product_matcher.get_product_by_id(product_id)
            if product:
                context.state = ConversationState.AWAITING_QUANTITY
                context.pending_items = context.pending_items or []
                context.pending_items.append({
                    "product": product,
                    "quantity": None
                })
                return {
                    "action": "send_text",
                    "message": f"Great choice! *{product.name}* - ${product.price:.2f}\n\n"
                              "How many units do you need?"
                }
        
        # Treat as search query
        result = self.product_matcher.match(message, max_results=5)
        if result.matches:
            return {
                "action": "send_products",
                "products": [
                    {
                        "product_id": m.product_id,
                        "name": m.clean_name,
                        "price": m.price
                    }
                    for m in result.matches
                ],
                "message": f"Found {result.total_found} products matching '{message}':"
            }
        
        return {
            "action": "send_text",
            "message": f"Sorry, I couldn't find any products matching '{message}'. "
                      "Please try a different search term or browse our catalog."
        }
    
    async def _handle_quantity_input(
        self,
        context: ConversationContext,
        message: str
    ) -> Dict[str, Any]:
        """Handle quantity input"""
        try:
            quantity = int(message.strip())
            if quantity <= 0:
                raise ValueError("Quantity must be positive")
            
            # Update pending item
            if context.pending_items:
                context.pending_items[-1]["quantity"] = quantity
            
            # Ask if they want to add more items
            context.state = ConversationState.AWAITING_CONFIRMATION
            
            return {
                "action": "send_interactive",
                "message": f"Added {quantity} units to your order.\n\n"
                          "Would you like to add more items or proceed to checkout?",
                "buttons": [
                    {"id": "add_more", "title": "Add More Items"},
                    {"id": "checkout", "title": "Checkout"},
                    {"id": "cancel_order", "title": "Cancel"}
                ]
            }
        
        except ValueError:
            return {
                "action": "send_text",
                "message": "Please enter a valid quantity (a positive number).\n\n"
                          "Example: _10_"
            }
    
    async def _handle_confirmation(
        self,
        context: ConversationContext,
        message: str
    ) -> Dict[str, Any]:
        """Handle order confirmation"""
        message_lower = message.lower().strip()
        
        if message_lower in ["confirm_order", "yes", "confirm", "proceed"]:
            # Check if we have delivery info
            if not context.extracted_order.get('delivery'):
                context.state = ConversationState.AWAITING_DELIVERY_INFO
                return {
                    "action": "send_text",
                    "message": "Great! Please provide your delivery details:\n\n"
                              "📍 Delivery address\n"
                              "📅 Preferred delivery date\n"
                              "📱 Contact number\n\n"
                              "Example: _123 Hougang Ave 1, #01-01, Singapore 530123. "
                              "Delivery next Monday. Contact: 91234567_"
                }
            
            # Order is confirmed
            context.state = ConversationState.ORDER_CONFIRMED
            order_id = context.extracted_order.get('order_id', 'TBD')
            
            return {
                "action": "order_confirmed",
                "order_id": order_id,
                "order": context.extracted_order,
                "message": f"✅ *Order Confirmed!*\n\n"
                          f"Order ID: *{order_id}*\n\n"
                          "We'll process your order and send you a Delivery Order (DO) shortly.\n\n"
                          "Thank you for ordering with UnidBox Hardware! 🙏"
            }
        
        elif message_lower in ["modify_order", "modify", "change"]:
            context.state = ConversationState.AWAITING_PRODUCT_SELECTION
            return {
                "action": "send_text",
                "message": "No problem! What would you like to change?\n\n"
                          "You can:\n"
                          "• Add more products\n"
                          "• Change quantities\n"
                          "• Remove items\n\n"
                          "Just tell me what you need!"
            }
        
        elif message_lower in ["cancel_order", "cancel", "no"]:
            context.state = ConversationState.IDLE
            context.extracted_order = None
            context.matched_products = None
            return {
                "action": "send_text",
                "message": "Order cancelled. No worries!\n\n"
                          "Feel free to start a new order anytime. Just tell me what you need! 😊"
            }
        
        elif message_lower in ["add_more"]:
            context.state = ConversationState.AWAITING_PRODUCT_SELECTION
            return {
                "action": "send_text",
                "message": "Sure! What else would you like to add?\n\n"
                          "Tell me the product name or search for items."
            }
        
        elif message_lower in ["checkout"]:
            # Proceed to delivery info
            context.state = ConversationState.AWAITING_DELIVERY_INFO
            return {
                "action": "send_text",
                "message": "Please provide your delivery details:\n\n"
                          "📍 Delivery address\n"
                          "📅 Preferred delivery date\n"
                          "📱 Contact number"
            }
        
        return {
            "action": "send_interactive",
            "message": "Please select an option:",
            "buttons": [
                {"id": "confirm_order", "title": "Confirm Order"},
                {"id": "modify_order", "title": "Modify Order"},
                {"id": "cancel_order", "title": "Cancel"}
            ]
        }
    
    async def _handle_delivery_info(
        self,
        context: ConversationContext,
        message: str
    ) -> Dict[str, Any]:
        """Handle delivery information input"""
        # Parse delivery info from message
        # In production, use AI to extract structured delivery info
        
        if context.extracted_order:
            context.extracted_order['delivery'] = {
                "address": message,
                "city": "Singapore",
                "notes": message
            }
        
        context.state = ConversationState.AWAITING_CONFIRMATION
        
        summary = self._build_order_summary_from_dict(context.extracted_order)
        
        return {
            "action": "send_interactive",
            "message": f"📋 *Final Order Summary*\n\n{summary}\n\n"
                      f"📍 Delivery: {message}\n\n"
                      "Ready to confirm?",
            "buttons": [
                {"id": "confirm_order", "title": "Confirm Order"},
                {"id": "modify_order", "title": "Modify"},
                {"id": "cancel_order", "title": "Cancel"}
            ]
        }
    
    def _get_or_create_context(self, phone_number: str) -> ConversationContext:
        """Get existing context or create new one"""
        if phone_number not in self.conversations:
            self.conversations[phone_number] = ConversationContext(
                phone_number=phone_number,
                state=ConversationState.IDLE
            )
        return self.conversations[phone_number]
    
    def reset_context(self, phone_number: str):
        """Reset conversation context for a phone number"""
        if phone_number in self.conversations:
            del self.conversations[phone_number]
    
    def _build_order_summary(self, order: ExtractedOrder) -> str:
        """Build a formatted order summary"""
        lines = []
        
        for item in order.items:
            price_str = f"${item.unit_price:.2f}" if item.unit_price > 0 else "TBD"
            total_str = f"${item.total_price:.2f}" if item.total_price > 0 else "TBD"
            lines.append(f"• {item.product_name}\n  Qty: {item.quantity} × {price_str} = {total_str}")
        
        summary = "\n".join(lines)
        summary += f"\n\n*Subtotal:* ${order.summary.subtotal:.2f}"
        
        if order.summary.tax > 0:
            summary += f"\n*GST (9%):* ${order.summary.tax:.2f}"
        
        if order.summary.shipping > 0:
            summary += f"\n*Shipping:* ${order.summary.shipping:.2f}"
        
        summary += f"\n*Total:* ${order.summary.total:.2f} SGD"
        
        return summary
    
    def _build_order_summary_from_dict(self, order_dict: Dict) -> str:
        """Build summary from order dictionary"""
        lines = []
        
        for item in order_dict.get('items', []):
            price = item.get('unit_price', 0)
            total = item.get('total_price', 0)
            price_str = f"${price:.2f}" if price > 0 else "TBD"
            total_str = f"${total:.2f}" if total > 0 else "TBD"
            lines.append(f"• {item.get('product_name', 'Unknown')}\n  Qty: {item.get('quantity', 0)} × {price_str} = {total_str}")
        
        summary_data = order_dict.get('summary', {})
        summary = "\n".join(lines)
        summary += f"\n\n*Subtotal:* ${summary_data.get('subtotal', 0):.2f}"
        
        if summary_data.get('tax', 0) > 0:
            summary += f"\n*GST (9%):* ${summary_data.get('tax', 0):.2f}"
        
        if summary_data.get('shipping', 0) > 0:
            summary += f"\n*Shipping:* ${summary_data.get('shipping', 0):.2f}"
        
        summary += f"\n*Total:* ${summary_data.get('total', 0):.2f} SGD"
        
        return summary
