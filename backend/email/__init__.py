# Email Notification Module for UnidBox Order Copilot
# This module handles email notifications for order events

from .email_client import EmailClient
from .templates import EmailTemplates
from .notification_service import NotificationService

__all__ = ['EmailClient', 'EmailTemplates', 'NotificationService']
