"""
Notification Service Module for UnidBox Order Copilot

This module orchestrates email notifications for various order events,
using the email client and templates.
"""

import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

from .email_client import EmailClient, EmailMessage, EmailAttachment, SendResult
from .templates import EmailTemplates, OrderData, OrderItem


@dataclass
class NotificationConfig:
    """Configuration for notification service"""
    admin_email: str = ""
    admin_name: str = "UnidBox Admin"
    support_email: str = ""
    send_admin_alerts: bool = True
    send_customer_emails: bool = True
    
    @classmethod
    def from_env(cls) -> 'NotificationConfig':
        """Create config from environment variables"""
        return cls(
            admin_email=os.getenv('ADMIN_EMAIL', 'admin@unidbox.com'),
            admin_name=os.getenv('ADMIN_NAME', 'UnidBox Admin'),
            support_email=os.getenv('SUPPORT_EMAIL', 'support@unidbox.com'),
            send_admin_alerts=os.getenv('SEND_ADMIN_ALERTS', 'true').lower() == 'true',
            send_customer_emails=os.getenv('SEND_CUSTOMER_EMAILS', 'true').lower() == 'true'
        )


class NotificationService:
    """
    Service for sending order-related email notifications.
    
    Handles notifications to both customers and admin for various
    order lifecycle events.
    """
    
    def __init__(
        self,
        email_client: Optional[EmailClient] = None,
        config: Optional[NotificationConfig] = None
    ):
        """
        Initialize the notification service.
        
        Args:
            email_client: EmailClient instance
            config: NotificationConfig instance
        """
        self.email_client = email_client or EmailClient()
        self.config = config or NotificationConfig.from_env()
    
    async def close(self):
        """Close the email client"""
        await self.email_client.close()
    
    def _order_dict_to_data(self, order_dict: Dict[str, Any]) -> OrderData:
        """Convert order dictionary to OrderData for templates"""
        items = []
        for item in order_dict.get('items', []):
            items.append(OrderItem(
                name=item.get('product_name', 'Unknown Product'),
                quantity=item.get('quantity', 0),
                unit_price=item.get('unit_price', 0),
                total_price=item.get('total_price', 0)
            ))
        
        summary = order_dict.get('summary', {})
        delivery = order_dict.get('delivery', {})
        
        return OrderData(
            order_id=order_dict.get('order_id', 'N/A'),
            items=items,
            subtotal=summary.get('subtotal', 0),
            tax=summary.get('tax', 0),
            shipping=summary.get('shipping', 0),
            total=summary.get('total', 0),
            customer_name=order_dict.get('customer_name'),
            customer_email=order_dict.get('customer_email'),
            customer_phone=order_dict.get('customer_contact'),
            delivery_address=delivery.get('address') if delivery else None,
            delivery_date=delivery.get('date') if delivery else None,
            order_date=order_dict.get('created_at', datetime.now().strftime('%Y-%m-%d')),
            status=order_dict.get('status', 'pending')
        )
    
    async def notify_order_confirmed(
        self,
        order: Dict[str, Any],
        customer_email: Optional[str] = None
    ) -> Dict[str, SendResult]:
        """
        Send order confirmation notifications.
        
        Args:
            order: Order dictionary
            customer_email: Customer email (overrides order data)
            
        Returns:
            Dictionary of send results for each notification
        """
        results = {}
        order_data = self._order_dict_to_data(order)
        
        # Send customer confirmation
        email = customer_email or order_data.customer_email
        if email and self.config.send_customer_emails:
            html = EmailTemplates.order_confirmation(order_data)
            message = EmailMessage(
                to=[email],
                subject=f"Order Confirmed - {order_data.order_id}",
                html_body=html,
                text_body=self._html_to_text(html)
            )
            results['customer'] = await self.email_client.send(message)
        
        # Send admin alert
        if self.config.send_admin_alerts and self.config.admin_email:
            html = EmailTemplates.new_order_admin_alert(order_data)
            message = EmailMessage(
                to=[self.config.admin_email],
                subject=f"🔔 New Order - {order_data.order_id} (${order_data.total:.2f})",
                html_body=html,
                text_body=self._html_to_text(html)
            )
            results['admin'] = await self.email_client.send(message)
        
        return results
    
    async def notify_order_shipped(
        self,
        order: Dict[str, Any],
        tracking_number: Optional[str] = None,
        customer_email: Optional[str] = None
    ) -> Dict[str, SendResult]:
        """
        Send order shipped notification.
        
        Args:
            order: Order dictionary
            tracking_number: Shipping tracking number
            customer_email: Customer email
            
        Returns:
            Dictionary of send results
        """
        results = {}
        order_data = self._order_dict_to_data(order)
        
        email = customer_email or order_data.customer_email
        if email and self.config.send_customer_emails:
            html = EmailTemplates.order_shipped(order_data, tracking_number)
            message = EmailMessage(
                to=[email],
                subject=f"Your Order is On Its Way! - {order_data.order_id}",
                html_body=html,
                text_body=self._html_to_text(html)
            )
            results['customer'] = await self.email_client.send(message)
        
        return results
    
    async def notify_order_delivered(
        self,
        order: Dict[str, Any],
        customer_email: Optional[str] = None
    ) -> Dict[str, SendResult]:
        """
        Send order delivered notification.
        
        Args:
            order: Order dictionary
            customer_email: Customer email
            
        Returns:
            Dictionary of send results
        """
        results = {}
        order_data = self._order_dict_to_data(order)
        
        email = customer_email or order_data.customer_email
        if email and self.config.send_customer_emails:
            html = EmailTemplates.order_delivered(order_data)
            message = EmailMessage(
                to=[email],
                subject=f"Order Delivered - {order_data.order_id}",
                html_body=html,
                text_body=self._html_to_text(html)
            )
            results['customer'] = await self.email_client.send(message)
        
        return results
    
    async def send_delivery_order(
        self,
        order: Dict[str, Any],
        do_pdf_content: bytes,
        customer_email: Optional[str] = None
    ) -> Dict[str, SendResult]:
        """
        Send Delivery Order PDF to customer.
        
        Args:
            order: Order dictionary
            do_pdf_content: PDF content as bytes
            customer_email: Customer email
            
        Returns:
            Dictionary of send results
        """
        results = {}
        order_data = self._order_dict_to_data(order)
        
        email = customer_email or order_data.customer_email
        if email and self.config.send_customer_emails:
            html = EmailTemplates.delivery_order_attached(order_data)
            
            attachment = EmailAttachment(
                filename=f"DO_{order_data.order_id}.pdf",
                content=do_pdf_content,
                content_type="application/pdf"
            )
            
            message = EmailMessage(
                to=[email],
                subject=f"Delivery Order - {order_data.order_id}",
                html_body=html,
                text_body=self._html_to_text(html),
                attachments=[attachment]
            )
            results['customer'] = await self.email_client.send(message)
        
        return results
    
    async def send_custom_notification(
        self,
        to: List[str],
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        attachments: Optional[List[EmailAttachment]] = None
    ) -> SendResult:
        """
        Send a custom notification email.
        
        Args:
            to: List of recipient emails
            subject: Email subject
            html_body: HTML content
            text_body: Plain text content
            attachments: List of attachments
            
        Returns:
            SendResult
        """
        message = EmailMessage(
            to=to,
            subject=subject,
            html_body=html_body,
            text_body=text_body or self._html_to_text(html_body),
            attachments=attachments
        )
        return await self.email_client.send(message)
    
    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text (basic implementation)"""
        import re
        
        # Remove style and script tags
        text = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
        
        # Replace common tags
        text = re.sub(r'<br\s*/?>', '\n', text)
        text = re.sub(r'<p[^>]*>', '\n', text)
        text = re.sub(r'</p>', '\n', text)
        text = re.sub(r'<tr[^>]*>', '\n', text)
        text = re.sub(r'<td[^>]*>', ' | ', text)
        text = re.sub(r'<th[^>]*>', ' | ', text)
        text = re.sub(r'<h[1-6][^>]*>', '\n\n', text)
        text = re.sub(r'</h[1-6]>', '\n', text)
        
        # Remove all remaining tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Clean up whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r' +', ' ', text)
        
        # Decode HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        
        return text.strip()


# Convenience functions for quick notifications

async def send_order_confirmation(order: Dict[str, Any], customer_email: str) -> Dict[str, SendResult]:
    """Quick function to send order confirmation"""
    service = NotificationService()
    try:
        return await service.notify_order_confirmed(order, customer_email)
    finally:
        await service.close()


async def send_order_shipped(order: Dict[str, Any], customer_email: str, tracking: Optional[str] = None) -> Dict[str, SendResult]:
    """Quick function to send shipped notification"""
    service = NotificationService()
    try:
        return await service.notify_order_shipped(order, tracking, customer_email)
    finally:
        await service.close()


async def send_delivery_order_email(order: Dict[str, Any], pdf_content: bytes, customer_email: str) -> Dict[str, SendResult]:
    """Quick function to send DO with PDF"""
    service = NotificationService()
    try:
        return await service.send_delivery_order(order, pdf_content, customer_email)
    finally:
        await service.close()
