"""
Email Templates Module for UnidBox Order Copilot

This module provides HTML email templates for various order notifications.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class OrderItem:
    """Order item for template rendering"""
    name: str
    quantity: int
    unit_price: float
    total_price: float


@dataclass
class OrderData:
    """Order data for template rendering"""
    order_id: str
    items: List[OrderItem]
    subtotal: float
    tax: float
    shipping: float
    total: float
    customer_name: str
    customer_email: Optional[str]
    customer_phone: Optional[str]
    delivery_address: Optional[str]
    delivery_date: Optional[str]
    order_date: str
    status: str


class EmailTemplates:
    """
    HTML email templates for UnidBox notifications.
    
    All templates use inline CSS for maximum email client compatibility.
    """
    
    # Brand colors
    PRIMARY_COLOR = "#1e3a5f"  # Navy blue
    SECONDARY_COLOR = "#f59e0b"  # Amber/Orange
    SUCCESS_COLOR = "#10b981"  # Green
    WARNING_COLOR = "#f59e0b"  # Amber
    ERROR_COLOR = "#ef4444"  # Red
    BACKGROUND_COLOR = "#f3f4f6"
    TEXT_COLOR = "#1f2937"
    
    @classmethod
    def base_template(cls, content: str, title: str = "UnidBox Hardware") -> str:
        """Base HTML template wrapper"""
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: {cls.BACKGROUND_COLOR};">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
        <tr>
            <td align="center" style="padding: 40px 0;">
                <table role="presentation" style="width: 600px; max-width: 100%; border-collapse: collapse; background-color: #ffffff; border-radius: 8px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="background-color: {cls.PRIMARY_COLOR}; padding: 30px; text-align: center; border-radius: 8px 8px 0 0;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: bold;">
                                UnidBox Hardware
                            </h1>
                            <p style="margin: 10px 0 0; color: rgba(255, 255, 255, 0.8); font-size: 14px;">
                                Your Trusted Hardware Partner Since 2015
                            </p>
                        </td>
                    </tr>
                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px 30px;">
                            {content}
                        </td>
                    </tr>
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f9fafb; padding: 30px; text-align: center; border-radius: 0 0 8px 8px; border-top: 1px solid #e5e7eb;">
                            <p style="margin: 0 0 10px; color: #6b7280; font-size: 14px;">
                                UnidBox Hardware Pte. Ltd.
                            </p>
                            <p style="margin: 0 0 10px; color: #6b7280; font-size: 12px;">
                                Hougang | Kovan | MacPherson | Bedok | Tampines
                            </p>
                            <p style="margin: 0; color: #9ca3af; font-size: 12px;">
                                © {datetime.now().year} UnidBox Hardware. All rights reserved.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
    
    @classmethod
    def order_confirmation(cls, order: OrderData) -> str:
        """Order confirmation email template"""
        items_html = ""
        for item in order.items:
            items_html += f"""
            <tr>
                <td style="padding: 12px; border-bottom: 1px solid #e5e7eb;">{item.name}</td>
                <td style="padding: 12px; border-bottom: 1px solid #e5e7eb; text-align: center;">{item.quantity}</td>
                <td style="padding: 12px; border-bottom: 1px solid #e5e7eb; text-align: right;">${item.unit_price:.2f}</td>
                <td style="padding: 12px; border-bottom: 1px solid #e5e7eb; text-align: right;">${item.total_price:.2f}</td>
            </tr>
            """
        
        delivery_section = ""
        if order.delivery_address:
            delivery_section = f"""
            <div style="background-color: #f9fafb; padding: 20px; border-radius: 8px; margin-top: 20px;">
                <h3 style="margin: 0 0 15px; color: {cls.PRIMARY_COLOR}; font-size: 16px;">📍 Delivery Information</h3>
                <p style="margin: 0 0 8px; color: {cls.TEXT_COLOR};">
                    <strong>Address:</strong> {order.delivery_address}
                </p>
                {f'<p style="margin: 0; color: {cls.TEXT_COLOR};"><strong>Preferred Date:</strong> {order.delivery_date}</p>' if order.delivery_date else ''}
            </div>
            """
        
        content = f"""
        <div style="text-align: center; margin-bottom: 30px;">
            <div style="display: inline-block; background-color: {cls.SUCCESS_COLOR}; color: white; padding: 10px 20px; border-radius: 50px; font-size: 14px; font-weight: bold;">
                ✓ Order Confirmed
            </div>
        </div>
        
        <h2 style="margin: 0 0 10px; color: {cls.TEXT_COLOR}; font-size: 24px;">Thank you for your order!</h2>
        <p style="margin: 0 0 20px; color: #6b7280; font-size: 16px;">
            Hi {order.customer_name or 'Valued Customer'},
        </p>
        <p style="margin: 0 0 30px; color: #6b7280; font-size: 16px;">
            We've received your order and it's being processed. Here are your order details:
        </p>
        
        <div style="background-color: {cls.PRIMARY_COLOR}; color: white; padding: 15px 20px; border-radius: 8px 8px 0 0;">
            <table style="width: 100%;">
                <tr>
                    <td>
                        <strong>Order ID:</strong> {order.order_id}
                    </td>
                    <td style="text-align: right;">
                        <strong>Date:</strong> {order.order_date}
                    </td>
                </tr>
            </table>
        </div>
        
        <table style="width: 100%; border-collapse: collapse; border: 1px solid #e5e7eb; border-top: none;">
            <thead>
                <tr style="background-color: #f9fafb;">
                    <th style="padding: 12px; text-align: left; color: {cls.TEXT_COLOR}; font-size: 14px;">Product</th>
                    <th style="padding: 12px; text-align: center; color: {cls.TEXT_COLOR}; font-size: 14px;">Qty</th>
                    <th style="padding: 12px; text-align: right; color: {cls.TEXT_COLOR}; font-size: 14px;">Price</th>
                    <th style="padding: 12px; text-align: right; color: {cls.TEXT_COLOR}; font-size: 14px;">Total</th>
                </tr>
            </thead>
            <tbody>
                {items_html}
            </tbody>
            <tfoot>
                <tr>
                    <td colspan="3" style="padding: 12px; text-align: right; color: #6b7280;">Subtotal</td>
                    <td style="padding: 12px; text-align: right; color: {cls.TEXT_COLOR};">${order.subtotal:.2f}</td>
                </tr>
                <tr>
                    <td colspan="3" style="padding: 12px; text-align: right; color: #6b7280;">GST (9%)</td>
                    <td style="padding: 12px; text-align: right; color: {cls.TEXT_COLOR};">${order.tax:.2f}</td>
                </tr>
                <tr>
                    <td colspan="3" style="padding: 12px; text-align: right; color: #6b7280;">Shipping</td>
                    <td style="padding: 12px; text-align: right; color: {cls.TEXT_COLOR};">${order.shipping:.2f}</td>
                </tr>
                <tr style="background-color: {cls.PRIMARY_COLOR};">
                    <td colspan="3" style="padding: 15px; text-align: right; color: white; font-weight: bold; font-size: 16px;">Total</td>
                    <td style="padding: 15px; text-align: right; color: white; font-weight: bold; font-size: 18px;">${order.total:.2f} SGD</td>
                </tr>
            </tfoot>
        </table>
        
        {delivery_section}
        
        <div style="margin-top: 30px; padding: 20px; background-color: #fef3c7; border-radius: 8px; border-left: 4px solid {cls.WARNING_COLOR};">
            <p style="margin: 0; color: #92400e; font-size: 14px;">
                <strong>What's Next?</strong><br>
                We'll send you a Delivery Order (DO) once your order is ready for dispatch. You can track your order status anytime by replying to this email or contacting us on WhatsApp.
            </p>
        </div>
        """
        
        return cls.base_template(content, f"Order Confirmation - {order.order_id}")
    
    @classmethod
    def order_shipped(cls, order: OrderData, tracking_number: Optional[str] = None) -> str:
        """Order shipped notification template"""
        tracking_section = ""
        if tracking_number:
            tracking_section = f"""
            <div style="background-color: #f0fdf4; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center;">
                <p style="margin: 0 0 10px; color: #166534; font-size: 14px;">Tracking Number</p>
                <p style="margin: 0; color: {cls.PRIMARY_COLOR}; font-size: 24px; font-weight: bold; letter-spacing: 2px;">
                    {tracking_number}
                </p>
            </div>
            """
        
        content = f"""
        <div style="text-align: center; margin-bottom: 30px;">
            <div style="display: inline-block; background-color: {cls.SECONDARY_COLOR}; color: white; padding: 10px 20px; border-radius: 50px; font-size: 14px; font-weight: bold;">
                📦 Order Shipped
            </div>
        </div>
        
        <h2 style="margin: 0 0 10px; color: {cls.TEXT_COLOR}; font-size: 24px;">Your order is on its way!</h2>
        <p style="margin: 0 0 20px; color: #6b7280; font-size: 16px;">
            Hi {order.customer_name or 'Valued Customer'},
        </p>
        <p style="margin: 0 0 30px; color: #6b7280; font-size: 16px;">
            Great news! Your order <strong>{order.order_id}</strong> has been shipped and is on its way to you.
        </p>
        
        {tracking_section}
        
        <div style="background-color: #f9fafb; padding: 20px; border-radius: 8px;">
            <h3 style="margin: 0 0 15px; color: {cls.PRIMARY_COLOR}; font-size: 16px;">📍 Delivery Details</h3>
            <p style="margin: 0 0 8px; color: {cls.TEXT_COLOR};">
                <strong>Address:</strong> {order.delivery_address or 'To be confirmed'}
            </p>
            <p style="margin: 0; color: {cls.TEXT_COLOR};">
                <strong>Expected Delivery:</strong> {order.delivery_date or 'Within 2-3 business days'}
            </p>
        </div>
        
        <div style="margin-top: 30px; text-align: center;">
            <p style="margin: 0; color: #6b7280; font-size: 14px;">
                Questions about your delivery? Contact us on WhatsApp or reply to this email.
            </p>
        </div>
        """
        
        return cls.base_template(content, f"Order Shipped - {order.order_id}")
    
    @classmethod
    def order_delivered(cls, order: OrderData) -> str:
        """Order delivered notification template"""
        content = f"""
        <div style="text-align: center; margin-bottom: 30px;">
            <div style="display: inline-block; background-color: {cls.SUCCESS_COLOR}; color: white; padding: 10px 20px; border-radius: 50px; font-size: 14px; font-weight: bold;">
                ✓ Order Delivered
            </div>
        </div>
        
        <h2 style="margin: 0 0 10px; color: {cls.TEXT_COLOR}; font-size: 24px;">Your order has been delivered!</h2>
        <p style="margin: 0 0 20px; color: #6b7280; font-size: 16px;">
            Hi {order.customer_name or 'Valued Customer'},
        </p>
        <p style="margin: 0 0 30px; color: #6b7280; font-size: 16px;">
            Your order <strong>{order.order_id}</strong> has been successfully delivered. We hope you're satisfied with your purchase!
        </p>
        
        <div style="background-color: #f0fdf4; padding: 30px; border-radius: 8px; text-align: center;">
            <p style="margin: 0 0 15px; color: #166534; font-size: 18px; font-weight: bold;">
                Thank you for choosing UnidBox Hardware!
            </p>
            <p style="margin: 0; color: #166534; font-size: 14px;">
                Your trusted partner for quality hardware supplies.
            </p>
        </div>
        
        <div style="margin-top: 30px; padding: 20px; background-color: #f9fafb; border-radius: 8px;">
            <h3 style="margin: 0 0 15px; color: {cls.PRIMARY_COLOR}; font-size: 16px;">Need Help?</h3>
            <p style="margin: 0; color: #6b7280; font-size: 14px;">
                If you have any questions about your order or need assistance with your products, don't hesitate to contact us. We're here to help!
            </p>
        </div>
        """
        
        return cls.base_template(content, f"Order Delivered - {order.order_id}")
    
    @classmethod
    def new_order_admin_alert(cls, order: OrderData) -> str:
        """Admin notification for new order"""
        items_html = ""
        for item in order.items:
            items_html += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb;">{item.name}</td>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb; text-align: center;">{item.quantity}</td>
                <td style="padding: 10px; border-bottom: 1px solid #e5e7eb; text-align: right;">${item.total_price:.2f}</td>
            </tr>
            """
        
        content = f"""
        <div style="text-align: center; margin-bottom: 30px;">
            <div style="display: inline-block; background-color: {cls.SECONDARY_COLOR}; color: white; padding: 10px 20px; border-radius: 50px; font-size: 14px; font-weight: bold;">
                🔔 New Order Received
            </div>
        </div>
        
        <h2 style="margin: 0 0 20px; color: {cls.TEXT_COLOR}; font-size: 24px;">New Order Alert</h2>
        
        <div style="background-color: #fef3c7; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
            <table style="width: 100%;">
                <tr>
                    <td style="color: #92400e;">
                        <strong>Order ID:</strong> {order.order_id}
                    </td>
                    <td style="text-align: right; color: #92400e;">
                        <strong>Total:</strong> ${order.total:.2f} SGD
                    </td>
                </tr>
            </table>
        </div>
        
        <h3 style="margin: 0 0 15px; color: {cls.PRIMARY_COLOR}; font-size: 16px;">Customer Details</h3>
        <table style="width: 100%; margin-bottom: 20px;">
            <tr>
                <td style="padding: 8px 0; color: #6b7280;">Name:</td>
                <td style="padding: 8px 0; color: {cls.TEXT_COLOR};">{order.customer_name or 'Not provided'}</td>
            </tr>
            <tr>
                <td style="padding: 8px 0; color: #6b7280;">Email:</td>
                <td style="padding: 8px 0; color: {cls.TEXT_COLOR};">{order.customer_email or 'Not provided'}</td>
            </tr>
            <tr>
                <td style="padding: 8px 0; color: #6b7280;">Phone:</td>
                <td style="padding: 8px 0; color: {cls.TEXT_COLOR};">{order.customer_phone or 'Not provided'}</td>
            </tr>
            <tr>
                <td style="padding: 8px 0; color: #6b7280;">Delivery:</td>
                <td style="padding: 8px 0; color: {cls.TEXT_COLOR};">{order.delivery_address or 'Not provided'}</td>
            </tr>
        </table>
        
        <h3 style="margin: 0 0 15px; color: {cls.PRIMARY_COLOR}; font-size: 16px;">Order Items</h3>
        <table style="width: 100%; border-collapse: collapse; border: 1px solid #e5e7eb;">
            <thead>
                <tr style="background-color: #f9fafb;">
                    <th style="padding: 10px; text-align: left;">Product</th>
                    <th style="padding: 10px; text-align: center;">Qty</th>
                    <th style="padding: 10px; text-align: right;">Total</th>
                </tr>
            </thead>
            <tbody>
                {items_html}
            </tbody>
        </table>
        
        <div style="margin-top: 30px; text-align: center;">
            <p style="margin: 0; color: #6b7280; font-size: 14px;">
                Please process this order and generate the Delivery Order.
            </p>
        </div>
        """
        
        return cls.base_template(content, f"New Order - {order.order_id}")
    
    @classmethod
    def delivery_order_attached(cls, order: OrderData) -> str:
        """Delivery Order email with DO attached"""
        content = f"""
        <div style="text-align: center; margin-bottom: 30px;">
            <div style="display: inline-block; background-color: {cls.PRIMARY_COLOR}; color: white; padding: 10px 20px; border-radius: 50px; font-size: 14px; font-weight: bold;">
                📄 Delivery Order
            </div>
        </div>
        
        <h2 style="margin: 0 0 10px; color: {cls.TEXT_COLOR}; font-size: 24px;">Your Delivery Order is Ready</h2>
        <p style="margin: 0 0 20px; color: #6b7280; font-size: 16px;">
            Hi {order.customer_name or 'Valued Customer'},
        </p>
        <p style="margin: 0 0 30px; color: #6b7280; font-size: 16px;">
            Please find attached the Delivery Order (DO) for your order <strong>{order.order_id}</strong>.
        </p>
        
        <div style="background-color: #f9fafb; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
            <table style="width: 100%;">
                <tr>
                    <td style="color: #6b7280;">Order ID:</td>
                    <td style="color: {cls.TEXT_COLOR}; font-weight: bold;">{order.order_id}</td>
                </tr>
                <tr>
                    <td style="color: #6b7280;">Order Date:</td>
                    <td style="color: {cls.TEXT_COLOR};">{order.order_date}</td>
                </tr>
                <tr>
                    <td style="color: #6b7280;">Total Amount:</td>
                    <td style="color: {cls.TEXT_COLOR}; font-weight: bold;">${order.total:.2f} SGD</td>
                </tr>
            </table>
        </div>
        
        <div style="background-color: #dbeafe; padding: 20px; border-radius: 8px; border-left: 4px solid #3b82f6;">
            <p style="margin: 0; color: #1e40af; font-size: 14px;">
                <strong>📎 Attachment:</strong> Delivery Order PDF<br><br>
                Please keep this document for your records. Present it upon delivery for verification.
            </p>
        </div>
        """
        
        return cls.base_template(content, f"Delivery Order - {order.order_id}")
