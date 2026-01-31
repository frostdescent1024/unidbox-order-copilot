"""
Email Client Module for UnidBox Order Copilot

This module provides email sending capabilities using SMTP or email APIs
like SendGrid, Mailgun, or AWS SES.
"""

import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
import httpx


class EmailProvider(Enum):
    """Supported email providers"""
    SMTP = "smtp"
    SENDGRID = "sendgrid"
    MAILGUN = "mailgun"
    AWS_SES = "aws_ses"


@dataclass
class EmailConfig:
    """Configuration for email sending"""
    provider: EmailProvider = EmailProvider.SMTP
    
    # SMTP settings
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    
    # API settings (for SendGrid, Mailgun, etc.)
    api_key: str = ""
    api_url: str = ""
    
    # Default sender
    default_from_email: str = ""
    default_from_name: str = "UnidBox Hardware"
    
    @classmethod
    def from_env(cls) -> 'EmailConfig':
        """Create config from environment variables"""
        provider = os.getenv('EMAIL_PROVIDER', 'smtp').lower()
        
        return cls(
            provider=EmailProvider(provider),
            smtp_host=os.getenv('SMTP_HOST', 'smtp.gmail.com'),
            smtp_port=int(os.getenv('SMTP_PORT', '587')),
            smtp_username=os.getenv('SMTP_USERNAME', ''),
            smtp_password=os.getenv('SMTP_PASSWORD', ''),
            smtp_use_tls=os.getenv('SMTP_USE_TLS', 'true').lower() == 'true',
            api_key=os.getenv('EMAIL_API_KEY', ''),
            api_url=os.getenv('EMAIL_API_URL', ''),
            default_from_email=os.getenv('EMAIL_FROM', 'orders@unidbox.com'),
            default_from_name=os.getenv('EMAIL_FROM_NAME', 'UnidBox Hardware')
        )


@dataclass
class EmailAttachment:
    """Email attachment"""
    filename: str
    content: bytes
    content_type: str = "application/octet-stream"


@dataclass
class EmailMessage:
    """Email message to send"""
    to: List[str]
    subject: str
    html_body: str
    text_body: Optional[str] = None
    from_email: Optional[str] = None
    from_name: Optional[str] = None
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    reply_to: Optional[str] = None
    attachments: Optional[List[EmailAttachment]] = None
    headers: Optional[Dict[str, str]] = None


@dataclass
class SendResult:
    """Result of sending an email"""
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None
    raw_response: Optional[Dict] = None


class EmailClient:
    """
    Client for sending emails via various providers.
    
    Supports SMTP, SendGrid, Mailgun, and AWS SES.
    """
    
    def __init__(self, config: Optional[EmailConfig] = None):
        """
        Initialize the email client.
        
        Args:
            config: EmailConfig instance, or loads from environment if None
        """
        self.config = config or EmailConfig.from_env()
        self._http_client: Optional[httpx.AsyncClient] = None
    
    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client for API-based providers"""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client
    
    async def close(self):
        """Close the HTTP client"""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
    
    async def send(self, message: EmailMessage) -> SendResult:
        """
        Send an email message.
        
        Args:
            message: EmailMessage to send
            
        Returns:
            SendResult with status and details
        """
        # Set defaults
        if not message.from_email:
            message.from_email = self.config.default_from_email
        if not message.from_name:
            message.from_name = self.config.default_from_name
        
        # Route to appropriate provider
        if self.config.provider == EmailProvider.SMTP:
            return await self._send_smtp(message)
        elif self.config.provider == EmailProvider.SENDGRID:
            return await self._send_sendgrid(message)
        elif self.config.provider == EmailProvider.MAILGUN:
            return await self._send_mailgun(message)
        else:
            return SendResult(
                success=False,
                error=f"Unsupported email provider: {self.config.provider}"
            )
    
    async def _send_smtp(self, message: EmailMessage) -> SendResult:
        """Send email via SMTP"""
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = message.subject
            msg["From"] = f"{message.from_name} <{message.from_email}>"
            msg["To"] = ", ".join(message.to)
            
            if message.cc:
                msg["Cc"] = ", ".join(message.cc)
            if message.reply_to:
                msg["Reply-To"] = message.reply_to
            
            # Add custom headers
            if message.headers:
                for key, value in message.headers.items():
                    msg[key] = value
            
            # Add body
            if message.text_body:
                msg.attach(MIMEText(message.text_body, "plain"))
            msg.attach(MIMEText(message.html_body, "html"))
            
            # Add attachments
            if message.attachments:
                for attachment in message.attachments:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.content)
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename={attachment.filename}"
                    )
                    msg.attach(part)
            
            # Get all recipients
            recipients = list(message.to)
            if message.cc:
                recipients.extend(message.cc)
            if message.bcc:
                recipients.extend(message.bcc)
            
            # Send via SMTP
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as server:
                if self.config.smtp_use_tls:
                    server.starttls(context=context)
                
                if self.config.smtp_username and self.config.smtp_password:
                    server.login(self.config.smtp_username, self.config.smtp_password)
                
                server.sendmail(message.from_email, recipients, msg.as_string())
            
            return SendResult(success=True, message_id="smtp_sent")
        
        except Exception as e:
            return SendResult(success=False, error=str(e))
    
    async def _send_sendgrid(self, message: EmailMessage) -> SendResult:
        """Send email via SendGrid API"""
        try:
            client = await self._get_http_client()
            
            # Build SendGrid payload
            payload = {
                "personalizations": [{
                    "to": [{"email": email} for email in message.to]
                }],
                "from": {
                    "email": message.from_email,
                    "name": message.from_name
                },
                "subject": message.subject,
                "content": [
                    {"type": "text/html", "value": message.html_body}
                ]
            }
            
            if message.text_body:
                payload["content"].insert(0, {"type": "text/plain", "value": message.text_body})
            
            if message.cc:
                payload["personalizations"][0]["cc"] = [{"email": email} for email in message.cc]
            
            if message.bcc:
                payload["personalizations"][0]["bcc"] = [{"email": email} for email in message.bcc]
            
            if message.reply_to:
                payload["reply_to"] = {"email": message.reply_to}
            
            # Send request
            response = await client.post(
                "https://api.sendgrid.com/v3/mail/send",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code in [200, 202]:
                message_id = response.headers.get("X-Message-Id", "sendgrid_sent")
                return SendResult(success=True, message_id=message_id)
            else:
                return SendResult(
                    success=False,
                    error=f"SendGrid error: {response.status_code}",
                    raw_response=response.json() if response.content else None
                )
        
        except Exception as e:
            return SendResult(success=False, error=str(e))
    
    async def _send_mailgun(self, message: EmailMessage) -> SendResult:
        """Send email via Mailgun API"""
        try:
            client = await self._get_http_client()
            
            # Build Mailgun payload
            data = {
                "from": f"{message.from_name} <{message.from_email}>",
                "to": message.to,
                "subject": message.subject,
                "html": message.html_body
            }
            
            if message.text_body:
                data["text"] = message.text_body
            
            if message.cc:
                data["cc"] = message.cc
            
            if message.bcc:
                data["bcc"] = message.bcc
            
            if message.reply_to:
                data["h:Reply-To"] = message.reply_to
            
            # Send request
            response = await client.post(
                self.config.api_url,
                data=data,
                auth=("api", self.config.api_key)
            )
            
            if response.status_code == 200:
                result = response.json()
                return SendResult(
                    success=True,
                    message_id=result.get("id"),
                    raw_response=result
                )
            else:
                return SendResult(
                    success=False,
                    error=f"Mailgun error: {response.status_code}",
                    raw_response=response.json() if response.content else None
                )
        
        except Exception as e:
            return SendResult(success=False, error=str(e))
    
    # Convenience methods
    
    async def send_simple(
        self,
        to: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ) -> SendResult:
        """Send a simple email to a single recipient"""
        message = EmailMessage(
            to=[to],
            subject=subject,
            html_body=html_body,
            text_body=text_body
        )
        return await self.send(message)
    
    async def send_with_attachment(
        self,
        to: str,
        subject: str,
        html_body: str,
        attachment_filename: str,
        attachment_content: bytes,
        attachment_type: str = "application/pdf"
    ) -> SendResult:
        """Send an email with a single attachment"""
        message = EmailMessage(
            to=[to],
            subject=subject,
            html_body=html_body,
            attachments=[
                EmailAttachment(
                    filename=attachment_filename,
                    content=attachment_content,
                    content_type=attachment_type
                )
            ]
        )
        return await self.send(message)
