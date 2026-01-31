"""
Order Extractor Module for UnidBox Order Copilot

This module extracts complete order details from parsed intents and matched products,
creating structured order data ready for confirmation and DO generation.
"""

import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime
from decimal import Decimal
import uuid


@dataclass
class OrderItem:
    """Represents a single item in an order"""
    product_id: str
    product_name: str
    quantity: int
    unit_price: float
    total_price: float
    brand: Optional[str] = None
    category: Optional[str] = None
    notes: Optional[str] = None
    match_confidence: float = 1.0


@dataclass
class OrderSummary:
    """Summary of order pricing"""
    subtotal: float
    discount: float = 0.0
    tax: float = 0.0
    shipping: float = 0.0
    total: float = 0.0
    currency: str = "SGD"


@dataclass
class DeliveryDetails:
    """Delivery information for an order"""
    address: str
    city: str = "Singapore"
    postal_code: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    preferred_date: Optional[str] = None
    preferred_time: Optional[str] = None
    instructions: Optional[str] = None


@dataclass
class ExtractedOrder:
    """Complete extracted order ready for confirmation"""
    order_id: str
    items: List[OrderItem]
    summary: OrderSummary
    delivery: Optional[DeliveryDetails]
    customer_name: Optional[str]
    customer_contact: Optional[str]
    raw_inquiry: str
    confidence_score: float
    needs_confirmation: bool
    confirmation_notes: List[str]
    created_at: str
    status: str = "draft"


class OrderExtractor:
    """
    Extracts complete order details from parsed intents and matched products.
    
    This class combines the parsed intent with matched products to create
    a structured order that can be confirmed by the dealer and admin.
    """
    
    # Default tax rate (GST in Singapore)
    DEFAULT_TAX_RATE = 0.09
    
    # Minimum order value for free shipping
    FREE_SHIPPING_THRESHOLD = 500.0
    
    # Default shipping cost
    DEFAULT_SHIPPING = 50.0
    
    def __init__(self, tax_rate: float = None, free_shipping_threshold: float = None):
        """
        Initialize the OrderExtractor.
        
        Args:
            tax_rate: Tax rate to apply (default 9% GST)
            free_shipping_threshold: Order value for free shipping
        """
        self.tax_rate = tax_rate if tax_rate is not None else self.DEFAULT_TAX_RATE
        self.free_shipping_threshold = free_shipping_threshold or self.FREE_SHIPPING_THRESHOLD
    
    def extract(
        self,
        parsed_intent: Dict[str, Any],
        matched_products: List[Dict[str, Any]],
        raw_message: str
    ) -> ExtractedOrder:
        """
        Extract a complete order from parsed intent and matched products.
        
        Args:
            parsed_intent: The parsed intent from IntentParser
            matched_products: List of matched products from ProductMatcher
            raw_message: The original dealer message
            
        Returns:
            ExtractedOrder with complete order details
        """
        # Generate order ID
        order_id = self._generate_order_id()
        
        # Extract order items
        items = self._extract_items(parsed_intent, matched_products)
        
        # Calculate summary
        summary = self._calculate_summary(items)
        
        # Extract delivery details
        delivery = self._extract_delivery(parsed_intent)
        
        # Determine confidence and confirmation needs
        confidence_score = self._calculate_confidence(parsed_intent, items)
        needs_confirmation, confirmation_notes = self._check_confirmation_needs(
            parsed_intent, items, delivery
        )
        
        return ExtractedOrder(
            order_id=order_id,
            items=items,
            summary=summary,
            delivery=delivery,
            customer_name=parsed_intent.get('customer_name'),
            customer_contact=parsed_intent.get('contact_info'),
            raw_inquiry=raw_message,
            confidence_score=confidence_score,
            needs_confirmation=needs_confirmation,
            confirmation_notes=confirmation_notes,
            created_at=datetime.utcnow().isoformat(),
            status="draft"
        )
    
    def _generate_order_id(self) -> str:
        """Generate a unique order ID"""
        timestamp = datetime.utcnow().strftime('%Y%m%d')
        unique_part = uuid.uuid4().hex[:6].upper()
        return f"UB-{timestamp}-{unique_part}"
    
    def _extract_items(
        self,
        parsed_intent: Dict[str, Any],
        matched_products: List[Dict[str, Any]]
    ) -> List[OrderItem]:
        """Extract order items from intent and matched products"""
        items = []
        
        # Get product intents from parsed intent
        product_intents = parsed_intent.get('products', [])
        
        # Match each product intent to a matched product
        for i, intent in enumerate(product_intents):
            quantity = intent.get('quantity', 1) or 1
            
            # Find corresponding matched product
            matched = None
            if i < len(matched_products):
                matched = matched_products[i]
            elif matched_products:
                # Try to find best match by name similarity
                matched = self._find_best_match(intent, matched_products)
            
            if matched:
                unit_price = matched.get('price', 0)
                items.append(OrderItem(
                    product_id=matched.get('product_id', ''),
                    product_name=matched.get('clean_name', matched.get('name', '')),
                    quantity=quantity,
                    unit_price=unit_price,
                    total_price=unit_price * quantity,
                    brand=matched.get('brand'),
                    category=matched.get('category'),
                    notes=intent.get('raw_text'),
                    match_confidence=matched.get('match_score', 0.5)
                ))
            else:
                # Create placeholder item for unmatched product
                items.append(OrderItem(
                    product_id='UNMATCHED',
                    product_name=intent.get('raw_text', 'Unknown Product'),
                    quantity=quantity,
                    unit_price=0,
                    total_price=0,
                    brand=intent.get('brand'),
                    category=intent.get('category'),
                    notes="Product not found in catalog - requires manual matching",
                    match_confidence=0
                ))
        
        return items
    
    def _find_best_match(
        self,
        intent: Dict[str, Any],
        matched_products: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Find the best matching product for an intent"""
        intent_brand = intent.get('brand', '').lower()
        intent_category = intent.get('category', '').lower()
        
        best_match = None
        best_score = 0
        
        for product in matched_products:
            score = product.get('match_score', 0)
            
            # Boost score if brand matches
            if intent_brand and intent_brand in product.get('name', '').lower():
                score += 0.2
            
            # Boost score if category matches
            if intent_category and intent_category == product.get('category', '').lower():
                score += 0.1
            
            if score > best_score:
                best_score = score
                best_match = product
        
        return best_match
    
    def _calculate_summary(self, items: List[OrderItem]) -> OrderSummary:
        """Calculate order summary with totals"""
        subtotal = sum(item.total_price for item in items)
        
        # Calculate shipping (free above threshold)
        shipping = 0.0 if subtotal >= self.free_shipping_threshold else self.DEFAULT_SHIPPING
        
        # Calculate tax
        tax = subtotal * self.tax_rate
        
        # Calculate total
        total = subtotal + tax + shipping
        
        return OrderSummary(
            subtotal=round(subtotal, 2),
            discount=0.0,
            tax=round(tax, 2),
            shipping=round(shipping, 2),
            total=round(total, 2),
            currency="SGD"
        )
    
    def _extract_delivery(self, parsed_intent: Dict[str, Any]) -> Optional[DeliveryDetails]:
        """Extract delivery details from parsed intent"""
        delivery_data = parsed_intent.get('delivery', {})
        
        if not delivery_data or not delivery_data.get('address'):
            return None
        
        return DeliveryDetails(
            address=delivery_data.get('address', ''),
            city="Singapore",
            postal_code=None,
            contact_name=parsed_intent.get('customer_name'),
            contact_phone=parsed_intent.get('contact_info'),
            preferred_date=delivery_data.get('date'),
            preferred_time=None,
            instructions=delivery_data.get('notes')
        )
    
    def _calculate_confidence(
        self,
        parsed_intent: Dict[str, Any],
        items: List[OrderItem]
    ) -> float:
        """Calculate overall confidence score for the order"""
        if not items:
            return 0.0
        
        # Average of item match confidences
        item_confidence = sum(item.match_confidence for item in items) / len(items)
        
        # Factor in intent parsing confidence
        intent_confidence = parsed_intent.get('confidence_score', 0.5)
        
        # Weighted average
        return round((item_confidence * 0.6 + intent_confidence * 0.4), 2)
    
    def _check_confirmation_needs(
        self,
        parsed_intent: Dict[str, Any],
        items: List[OrderItem],
        delivery: Optional[DeliveryDetails]
    ) -> tuple:
        """Check what needs confirmation before order can proceed"""
        needs_confirmation = False
        notes = []
        
        # Check for unmatched products
        unmatched = [item for item in items if item.product_id == 'UNMATCHED']
        if unmatched:
            needs_confirmation = True
            notes.append(f"{len(unmatched)} product(s) could not be matched - manual selection required")
        
        # Check for low confidence matches
        low_confidence = [item for item in items if item.match_confidence < 0.7 and item.product_id != 'UNMATCHED']
        if low_confidence:
            needs_confirmation = True
            notes.append(f"{len(low_confidence)} product(s) have low match confidence - please verify")
        
        # Check for missing quantities
        missing_qty = [item for item in items if item.quantity <= 0]
        if missing_qty:
            needs_confirmation = True
            notes.append("Some items are missing quantities")
        
        # Check for missing delivery info
        if not delivery:
            needs_confirmation = True
            notes.append("Delivery address required")
        
        # Check if intent parsing flagged clarification needed
        if parsed_intent.get('needs_clarification'):
            needs_confirmation = True
            notes.extend(parsed_intent.get('clarification_questions', []))
        
        return needs_confirmation, notes
    
    def apply_discount(self, order: ExtractedOrder, discount_percent: float) -> ExtractedOrder:
        """Apply a discount to an order"""
        discount_amount = order.summary.subtotal * (discount_percent / 100)
        
        new_summary = OrderSummary(
            subtotal=order.summary.subtotal,
            discount=round(discount_amount, 2),
            tax=round((order.summary.subtotal - discount_amount) * self.tax_rate, 2),
            shipping=order.summary.shipping,
            total=round(
                order.summary.subtotal - discount_amount + 
                (order.summary.subtotal - discount_amount) * self.tax_rate + 
                order.summary.shipping,
                2
            ),
            currency=order.summary.currency
        )
        
        order.summary = new_summary
        return order
    
    def confirm_order(self, order: ExtractedOrder) -> ExtractedOrder:
        """Mark an order as confirmed"""
        order.status = "confirmed"
        order.needs_confirmation = False
        return order
    
    def to_dict(self, order: ExtractedOrder) -> Dict[str, Any]:
        """Convert ExtractedOrder to dictionary for JSON serialization"""
        return {
            "order_id": order.order_id,
            "items": [asdict(item) for item in order.items],
            "summary": asdict(order.summary),
            "delivery": asdict(order.delivery) if order.delivery else None,
            "customer_name": order.customer_name,
            "customer_contact": order.customer_contact,
            "raw_inquiry": order.raw_inquiry,
            "confidence_score": order.confidence_score,
            "needs_confirmation": order.needs_confirmation,
            "confirmation_notes": order.confirmation_notes,
            "created_at": order.created_at,
            "status": order.status
        }
    
    def from_dict(self, data: Dict[str, Any]) -> ExtractedOrder:
        """Create ExtractedOrder from dictionary"""
        items = [OrderItem(**item) for item in data.get('items', [])]
        summary = OrderSummary(**data.get('summary', {}))
        delivery = DeliveryDetails(**data['delivery']) if data.get('delivery') else None
        
        return ExtractedOrder(
            order_id=data['order_id'],
            items=items,
            summary=summary,
            delivery=delivery,
            customer_name=data.get('customer_name'),
            customer_contact=data.get('customer_contact'),
            raw_inquiry=data.get('raw_inquiry', ''),
            confidence_score=data.get('confidence_score', 0),
            needs_confirmation=data.get('needs_confirmation', True),
            confirmation_notes=data.get('confirmation_notes', []),
            created_at=data.get('created_at', datetime.utcnow().isoformat()),
            status=data.get('status', 'draft')
        )
