"""
Delivery Order Generator Module for UnidBox Order Copilot

This module generates Delivery Order (DO) documents from confirmed orders,
including all necessary details for delivery and record-keeping.
"""

import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class DOItem:
    """Item in a Delivery Order"""
    line_number: int
    product_id: str
    product_name: str
    description: Optional[str]
    quantity: int
    unit: str = "pcs"
    unit_price: float = 0.0
    total_price: float = 0.0
    remarks: Optional[str] = None


@dataclass
class DOAddress:
    """Address for Delivery Order"""
    name: str
    company: Optional[str] = None
    address_line1: str = ""
    address_line2: Optional[str] = None
    city: str = "Singapore"
    postal_code: Optional[str] = None
    country: str = "Singapore"
    phone: Optional[str] = None
    email: Optional[str] = None


@dataclass
class DeliveryOrder:
    """Complete Delivery Order document"""
    do_number: str
    order_id: str
    
    # Dates
    issue_date: str
    delivery_date: Optional[str]
    
    # Parties
    ship_from: DOAddress
    ship_to: DOAddress
    bill_to: Optional[DOAddress] = None
    
    # Items
    items: List[DOItem] = field(default_factory=list)
    
    # Totals
    subtotal: float = 0.0
    tax_rate: float = 0.09
    tax_amount: float = 0.0
    shipping_cost: float = 0.0
    total: float = 0.0
    currency: str = "SGD"
    
    # Additional info
    payment_terms: str = "Net 30"
    delivery_terms: str = "Door-to-door delivery"
    special_instructions: Optional[str] = None
    
    # Status
    status: str = "pending"  # pending, shipped, delivered, cancelled
    created_at: str = ""
    updated_at: str = ""
    
    # Signatures
    prepared_by: Optional[str] = None
    approved_by: Optional[str] = None
    received_by: Optional[str] = None
    received_date: Optional[str] = None


class DeliveryOrderGenerator:
    """
    Generates Delivery Order documents from confirmed orders.
    
    This class handles the creation of structured DO data that can
    be rendered to PDF or other formats.
    """
    
    # Company information
    COMPANY_INFO = DOAddress(
        name="UnidBox Hardware Pte. Ltd.",
        company="UnidBox Hardware",
        address_line1="123 Hardware Street",
        address_line2="#01-01",
        city="Singapore",
        postal_code="123456",
        country="Singapore",
        phone="+65 6123 4567",
        email="orders@unidbox.com"
    )
    
    def __init__(self, company_info: Optional[DOAddress] = None):
        """
        Initialize the DO generator.
        
        Args:
            company_info: Company address info (uses default if not provided)
        """
        self.company_info = company_info or self.COMPANY_INFO
    
    def generate(self, order: Dict[str, Any]) -> DeliveryOrder:
        """
        Generate a Delivery Order from a confirmed order.
        
        Args:
            order: Order dictionary from OrderExtractor
            
        Returns:
            DeliveryOrder object
        """
        # Generate DO number
        do_number = self._generate_do_number()
        
        # Parse delivery info
        delivery_data = order.get('delivery', {}) or {}
        
        # Create ship-to address
        ship_to = DOAddress(
            name=order.get('customer_name') or 'Customer',
            address_line1=delivery_data.get('address', ''),
            city=delivery_data.get('city', 'Singapore'),
            postal_code=delivery_data.get('postal_code'),
            phone=order.get('customer_contact'),
            email=order.get('customer_email')
        )
        
        # Create items
        items = []
        for i, item in enumerate(order.get('items', []), 1):
            items.append(DOItem(
                line_number=i,
                product_id=item.get('product_id', ''),
                product_name=item.get('product_name', 'Unknown Product'),
                description=item.get('notes'),
                quantity=item.get('quantity', 0),
                unit="pcs",
                unit_price=item.get('unit_price', 0),
                total_price=item.get('total_price', 0),
                remarks=item.get('remarks')
            ))
        
        # Get summary
        summary = order.get('summary', {})
        
        now = datetime.utcnow()
        
        return DeliveryOrder(
            do_number=do_number,
            order_id=order.get('order_id', ''),
            issue_date=now.strftime('%Y-%m-%d'),
            delivery_date=delivery_data.get('date'),
            ship_from=self.company_info,
            ship_to=ship_to,
            bill_to=ship_to,  # Same as ship_to by default
            items=items,
            subtotal=summary.get('subtotal', 0),
            tax_rate=0.09,
            tax_amount=summary.get('tax', 0),
            shipping_cost=summary.get('shipping', 0),
            total=summary.get('total', 0),
            currency=summary.get('currency', 'SGD'),
            payment_terms="Net 30",
            delivery_terms="Door-to-door delivery",
            special_instructions=delivery_data.get('notes'),
            status="pending",
            created_at=now.isoformat(),
            updated_at=now.isoformat(),
            prepared_by="Order Copilot System"
        )
    
    def _generate_do_number(self) -> str:
        """Generate a unique DO number"""
        timestamp = datetime.utcnow().strftime('%Y%m%d')
        unique_part = uuid.uuid4().hex[:6].upper()
        return f"DO-{timestamp}-{unique_part}"
    
    def update_status(self, do: DeliveryOrder, status: str) -> DeliveryOrder:
        """Update DO status"""
        do.status = status
        do.updated_at = datetime.utcnow().isoformat()
        return do
    
    def mark_shipped(self, do: DeliveryOrder) -> DeliveryOrder:
        """Mark DO as shipped"""
        return self.update_status(do, "shipped")
    
    def mark_delivered(
        self,
        do: DeliveryOrder,
        received_by: Optional[str] = None
    ) -> DeliveryOrder:
        """Mark DO as delivered"""
        do.status = "delivered"
        do.received_by = received_by
        do.received_date = datetime.utcnow().strftime('%Y-%m-%d')
        do.updated_at = datetime.utcnow().isoformat()
        return do
    
    def to_dict(self, do: DeliveryOrder) -> Dict[str, Any]:
        """Convert DeliveryOrder to dictionary"""
        return {
            "do_number": do.do_number,
            "order_id": do.order_id,
            "issue_date": do.issue_date,
            "delivery_date": do.delivery_date,
            "ship_from": {
                "name": do.ship_from.name,
                "company": do.ship_from.company,
                "address_line1": do.ship_from.address_line1,
                "address_line2": do.ship_from.address_line2,
                "city": do.ship_from.city,
                "postal_code": do.ship_from.postal_code,
                "country": do.ship_from.country,
                "phone": do.ship_from.phone,
                "email": do.ship_from.email
            },
            "ship_to": {
                "name": do.ship_to.name,
                "company": do.ship_to.company,
                "address_line1": do.ship_to.address_line1,
                "address_line2": do.ship_to.address_line2,
                "city": do.ship_to.city,
                "postal_code": do.ship_to.postal_code,
                "country": do.ship_to.country,
                "phone": do.ship_to.phone,
                "email": do.ship_to.email
            },
            "items": [
                {
                    "line_number": item.line_number,
                    "product_id": item.product_id,
                    "product_name": item.product_name,
                    "description": item.description,
                    "quantity": item.quantity,
                    "unit": item.unit,
                    "unit_price": item.unit_price,
                    "total_price": item.total_price,
                    "remarks": item.remarks
                }
                for item in do.items
            ],
            "subtotal": do.subtotal,
            "tax_rate": do.tax_rate,
            "tax_amount": do.tax_amount,
            "shipping_cost": do.shipping_cost,
            "total": do.total,
            "currency": do.currency,
            "payment_terms": do.payment_terms,
            "delivery_terms": do.delivery_terms,
            "special_instructions": do.special_instructions,
            "status": do.status,
            "created_at": do.created_at,
            "updated_at": do.updated_at,
            "prepared_by": do.prepared_by,
            "approved_by": do.approved_by,
            "received_by": do.received_by,
            "received_date": do.received_date
        }
    
    def from_dict(self, data: Dict[str, Any]) -> DeliveryOrder:
        """Create DeliveryOrder from dictionary"""
        ship_from_data = data.get('ship_from', {})
        ship_to_data = data.get('ship_to', {})
        
        ship_from = DOAddress(
            name=ship_from_data.get('name', ''),
            company=ship_from_data.get('company'),
            address_line1=ship_from_data.get('address_line1', ''),
            address_line2=ship_from_data.get('address_line2'),
            city=ship_from_data.get('city', 'Singapore'),
            postal_code=ship_from_data.get('postal_code'),
            country=ship_from_data.get('country', 'Singapore'),
            phone=ship_from_data.get('phone'),
            email=ship_from_data.get('email')
        )
        
        ship_to = DOAddress(
            name=ship_to_data.get('name', ''),
            company=ship_to_data.get('company'),
            address_line1=ship_to_data.get('address_line1', ''),
            address_line2=ship_to_data.get('address_line2'),
            city=ship_to_data.get('city', 'Singapore'),
            postal_code=ship_to_data.get('postal_code'),
            country=ship_to_data.get('country', 'Singapore'),
            phone=ship_to_data.get('phone'),
            email=ship_to_data.get('email')
        )
        
        items = [
            DOItem(
                line_number=item.get('line_number', 0),
                product_id=item.get('product_id', ''),
                product_name=item.get('product_name', ''),
                description=item.get('description'),
                quantity=item.get('quantity', 0),
                unit=item.get('unit', 'pcs'),
                unit_price=item.get('unit_price', 0),
                total_price=item.get('total_price', 0),
                remarks=item.get('remarks')
            )
            for item in data.get('items', [])
        ]
        
        return DeliveryOrder(
            do_number=data.get('do_number', ''),
            order_id=data.get('order_id', ''),
            issue_date=data.get('issue_date', ''),
            delivery_date=data.get('delivery_date'),
            ship_from=ship_from,
            ship_to=ship_to,
            items=items,
            subtotal=data.get('subtotal', 0),
            tax_rate=data.get('tax_rate', 0.09),
            tax_amount=data.get('tax_amount', 0),
            shipping_cost=data.get('shipping_cost', 0),
            total=data.get('total', 0),
            currency=data.get('currency', 'SGD'),
            payment_terms=data.get('payment_terms', 'Net 30'),
            delivery_terms=data.get('delivery_terms', ''),
            special_instructions=data.get('special_instructions'),
            status=data.get('status', 'pending'),
            created_at=data.get('created_at', ''),
            updated_at=data.get('updated_at', ''),
            prepared_by=data.get('prepared_by'),
            approved_by=data.get('approved_by'),
            received_by=data.get('received_by'),
            received_date=data.get('received_date')
        )
