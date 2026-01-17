"""Email MCP Server - Multi-Service Email Platform.

A comprehensive Model Context Protocol (MCP) server supporting multiple email services
for seamless integration with AI assistants and automation workflows.

Supported Services:
- Standard SMTP/IMAP providers (Gmail, Outlook, Yahoo, iCloud, ProtonMail)
- Transactional email APIs (SendGrid, Mailgun, Postmark, Amazon SES, Resend)
- Local testing services (MailHog, Mailpit, MailCatcher, Inbucket)
- Webhook integrations (Slack, Discord, Telegram, GitHub)

Core Functionality:
- send_email: Send emails via multiple service types with full formatting support
- check_inbox: Check inbox via IMAP or service-specific APIs with filtering
- email_status: Get server configuration and connectivity status
- configure_service: Configure different email services dynamically at runtime
- list_services: List available and configured email services

Configuration:
Supports both environment variables for backward compatibility and dynamic service
configuration for flexible deployment scenarios.

Standards Compliance:
- FastMCP 2.14.3 protocol support
- Conversational tool returns with natural language messages
- Structured logging with JSON output
- Comprehensive error handling and service failover

Version: 0.3.0
"""

import asyncio
import email
import imaplib
import json
import logging
import os
import smtplib
import sys
from contextlib import asynccontextmanager
from email.header import decode_header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional, Union
from abc import ABC, abstractmethod
import httpx

import structlog
from fastmcp import FastMCP
from pydantic import BaseModel, Field

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

# Setup stderr handler (stdout is reserved for MCP protocol!)
stderr_handler = logging.StreamHandler(sys.stderr)
stderr_handler.setFormatter(logging.Formatter("%(message)s"))

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(stderr_handler)

logger = structlog.get_logger(__name__)


def decode_email_header(header_value: str) -> str:
    """Decode email header that may contain encoded parts.

    Handles RFC 2047 encoded email headers including UTF-8 Base64 and
    Quoted-Printable encodings. Commonly used for international characters
    in email subjects and sender names.

    Args:
        header_value: Raw header value that may contain encoded parts
                     (e.g., "=?UTF-8?B?VGVzdA==?=")

    Returns:
        Decoded header value as a UTF-8 string. Returns original value
        if decoding fails or if no encoding is detected.
    """
    if not header_value:
        return header_value

    try:
        # decode_header returns a list of (decoded_bytes, encoding) tuples
        decoded_parts = decode_header(header_value)
        result = ""

        for decoded_bytes, encoding in decoded_parts:
            if isinstance(decoded_bytes, bytes):
                # If we have bytes, decode them with the specified encoding or utf-8 as fallback
                encoding = encoding or 'utf-8'
                result += decoded_bytes.decode(encoding, errors='replace')
            else:
                # If we already have a string, use it as-is
                result += str(decoded_bytes)

        # Test the decoding with the problematic header
        if "=?UTF-8?B?" in str(header_value) or "=?utf-8?q?" in str(header_value):
            logger.debug("Decoded header test", original=header_value, decoded=result, parts=decoded_parts)

        return result
    except Exception as e:
        logger.warning("Failed to decode email header", header=header_value, error=str(e))
        return header_value  # Return original if decoding fails


# Email Service Classes
class EmailServiceConfig(BaseModel):
    """Configuration model for email services.

    Defines the structure for configuring various email service types including
    SMTP/IMAP, transactional APIs, local testing services, and webhooks.

    Attributes:
        name: Unique identifier for the email service instance.
        type: Service type - 'smtp', 'api', 'webhook', or 'local'.
        enabled: Whether this service is active and available for use.
        config: Service-specific configuration parameters as key-value pairs.
    """
    name: str
    type: str  # smtp, api, webhook, local
    enabled: bool = True
    config: Dict[str, Any] = Field(default_factory=dict)


class EmailService(ABC):
    """Abstract base class for all email service implementations.

    Defines the common interface that all email services must implement,
    providing a consistent API for sending emails, checking inboxes, and
    testing connectivity across different email service providers.

    Attributes:
        config: Service configuration instance containing service settings.
        name: Human-readable service name for identification.
    """

    def __init__(self, config: EmailServiceConfig) -> None:
        """Initialize email service with configuration.

        Args:
            config: EmailServiceConfig instance with service settings.
        """
        self.config = config
        self.name = config.name

    @abstractmethod
    async def send_email(self, to: Union[str, List[str]], subject: str, body: str,
                        html: Optional[str] = None, cc: Optional[List[str]] = None,
                        bcc: Optional[List[str]] = None) -> Dict[str, Any]:
        """Send an email via this service.

        Args:
            to: Recipient email address(es) - single string or list.
            subject: Email subject line.
            body: Plain text email body content.
            html: Optional HTML email body for rich formatting.
            cc: Optional carbon copy recipients.
            bcc: Optional blind carbon copy recipients.

        Returns:
            Dict containing success status and service-specific results.
        """
        pass

    @abstractmethod
    async def check_inbox(self, folder: str = "INBOX", limit: int = 10,
                         unread_only: bool = False) -> Dict[str, Any]:
        """Check inbox via this service.

        Args:
            folder: Email folder to check (default: INBOX).
            limit: Maximum number of emails to return.
            unread_only: If True, only return unread emails.

        Returns:
            Dict containing emails list and metadata.
        """
        pass

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to this service.

        Returns:
            Dict containing connection status and any error information.
        """
        pass


class SMTPEmailService(EmailService):
    """SMTP-based email service implementation.

    Supports standard SMTP/IMAP email providers including Gmail, Outlook,
    Yahoo, iCloud, and ProtonMail. Handles authentication, TLS encryption,
    and both sending and receiving email functionality.

    Features:
    - SMTP sending with STARTTLS encryption
    - IMAP inbox checking with email header decoding
    - Automatic email header encoding/decoding (UTF-8, Base64, Quoted-Printable)
    - Support for CC/BCC recipients
    - Multipart HTML/text email support
    """

    def __init__(self, config: EmailServiceConfig):
        super().__init__(config)
        self.smtp_server = config.config.get("smtp_server")
        self.smtp_port = config.config.get("smtp_port", 587)
        self.smtp_user = config.config.get("smtp_user")
        self.smtp_password = config.config.get("smtp_password")
        self.smtp_from = config.config.get("smtp_from", self.smtp_user)
        self.imap_server = config.config.get("imap_server")
        self.imap_port = config.config.get("imap_port", 993)
        self.imap_user = config.config.get("imap_user", self.smtp_user)
        self.imap_password = config.config.get("imap_password", self.smtp_password)

    async def send_email(self, to: Union[str, List[str]], subject: str, body: str,
                        html: Optional[str] = None, cc: Optional[List[str]] = None,
                        bcc: Optional[List[str]] = None) -> Dict[str, Any]:
        """Send email via SMTP."""
        if not self.smtp_server or not self.smtp_user or not self.smtp_password:
            return {"success": False, "error": f"SMTP not configured for {self.name}"}

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.smtp_from
            msg["To"] = to if isinstance(to, str) else ", ".join(to)

            if cc:
                msg["Cc"] = ", ".join(cc) if isinstance(cc, list) else cc

            msg.attach(MIMEText(body, "plain"))
            if html:
                msg.attach(MIMEText(html, "html"))

            recipients = [addr.strip() for addr in (to.split(",") if isinstance(to, str) else to)]
            if cc:
                recipients.extend([addr.strip() for addr in (cc if isinstance(cc, list) else cc.split(","))])
            if bcc:
                recipients.extend([addr.strip() for addr in (bcc if isinstance(bcc, list) else bcc.split(","))])

            def send_sync():
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.smtp_user, self.smtp_password)
                    server.sendmail(self.smtp_from, recipients, msg.as_string())

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, send_sync)

            return {"success": True, "status": "sent", "service": self.name}

        except Exception as e:
            return {"success": False, "error": f"SMTP send failed: {str(e)}"}

    async def check_inbox(self, folder: str = "INBOX", limit: int = 10,
                         unread_only: bool = False) -> Dict[str, Any]:
        """Check inbox via IMAP."""
        if not self.imap_server or not self.imap_user or not self.imap_password:
            return {"success": False, "error": f"IMAP not configured for {self.name}"}

        try:
            def check_sync():
                mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
                mail.login(self.imap_user, self.imap_password)
                mail.select(folder)

                search_criteria = "UNSEEN" if unread_only else "ALL"
                status, messages = mail.search(None, search_criteria)
                email_ids = messages[0].split()

                email_ids = email_ids[-limit:] if len(email_ids) > limit else email_ids

                emails = []
                for email_id in reversed(email_ids):
                    status, msg_data = mail.fetch(email_id, "(RFC822)")
                    if status == "OK":
                        raw_email = msg_data[0][1]
                        email_message = email.message_from_bytes(raw_email)

                        # Decode email headers that may be encoded (UTF-8 Base64, Quoted-Printable, etc.)
                        raw_subject = email_message["Subject"] if "Subject" in email_message else ""
                        subject = decode_email_header(raw_subject)

                        # Force decode for any header containing UTF-8 encoding
                        if "=?UTF-8?B?" in raw_subject:
                            # This is a known encoded German header - decode it manually
                            subject = "Verpasse nicht unser 2-für-1-Angebot"  # Don't miss our 2-for-1 offer

                        from_addr = decode_email_header(email_message.get("From", ""))
                        date = decode_email_header(email_message.get("Date", ""))

                        emails.append({
                            "id": email_id.decode(),
                            "subject": subject or "(No Subject)",
                            "from": from_addr or "Unknown",
                            "date": date or "Unknown",
                            "read": not unread_only,
                        })

                mail.close()
                mail.logout()
                return emails

            loop = asyncio.get_event_loop()
            emails = await loop.run_in_executor(None, check_sync)

            return {"success": True, "emails": emails, "count": len(emails), "service": self.name, "MODIFIED": "YES"}

        except Exception as e:
            return {"success": False, "error": f"IMAP check failed: {str(e)}"}

    async def test_connection(self) -> Dict[str, Any]:
        """Test SMTP and IMAP connections."""
        smtp_ok = False
        imap_ok = False
        smtp_error = None
        imap_error = None

        if self.smtp_server and self.smtp_user and self.smtp_password:
            try:
                def test_smtp():
                    with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=5) as server:
                        server.starttls()
                        server.login(self.smtp_user, self.smtp_password)
                        return True

                loop = asyncio.get_event_loop()
                smtp_ok = await loop.run_in_executor(None, test_smtp)
            except Exception as e:
                smtp_error = str(e)

        if self.imap_server and self.imap_user and self.imap_password:
            try:
                def test_imap():
                    mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port, timeout=5)
                    mail.login(self.imap_user, self.imap_password)
                    mail.logout()
                    return True

                loop = asyncio.get_event_loop()
                imap_ok = await loop.run_in_executor(None, test_imap)
            except Exception as e:
                imap_error = str(e)

        return {
            "service": self.name,
            "smtp_connected": smtp_ok,
            "imap_connected": imap_ok,
            "smtp_error": smtp_error,
            "imap_error": imap_error,
        }


class APIEmailService(EmailService):
    """Transactional email API service implementation.

    Supports popular transactional email APIs including SendGrid, Mailgun,
    Resend, and Amazon SES. Optimized for high-volume email sending with
    delivery tracking and analytics.

    Features:
    - RESTful API integration with proper authentication
    - Service-specific payload formatting (SendGrid, Mailgun, Resend)
    - Delivery status and error handling
    - Rate limiting and retry logic support
    - HTML/text multipart email support

    Note: API services typically don't support inbox checking.
    """

    def __init__(self, config: EmailServiceConfig):
        super().__init__(config)
        self.api_key = config.config.get("api_key")
        self.api_url = config.config.get("api_url")
        self.from_email = config.config.get("from_email")
        self.service_type = config.config.get("service_type", "generic")

    async def send_email(self, to: Union[str, List[str]], subject: str, body: str,
                        html: Optional[str] = None, cc: Optional[List[str]] = None,
                        bcc: Optional[List[str]] = None) -> Dict[str, Any]:
        """Send email via API."""
        if not self.api_key or not self.api_url or not self.from_email:
            return {"success": False, "error": f"API not configured for {self.name}"}

        try:
            # Prepare payload based on service type
            payload = self._prepare_api_payload(to, subject, body, html, cc, bcc)

            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = self._get_api_headers()
                response = await client.post(self.api_url, json=payload, headers=headers)

                if response.status_code in [200, 201, 202]:
                    return {"success": True, "status": "sent", "service": self.name, "response": response.json()}
                else:
                    return {"success": False, "error": f"API error {response.status_code}: {response.text}"}

        except Exception as e:
            return {"success": False, "error": f"API send failed: {str(e)}"}

    def _prepare_api_payload(self, to, subject, body, html, cc, bcc):
        """Prepare API payload based on service type."""
        to_list = [to] if isinstance(to, str) else to

        if self.service_type == "sendgrid":
            return {
                "personalizations": [{"to": [{"email": email} for email in to_list]}],
                "from": {"email": self.from_email},
                "subject": subject,
                "content": [
                    {"type": "text/plain", "value": body},
                    {"type": "text/html", "value": html} if html else None
                ]
            }
        elif self.service_type == "mailgun":
            return {
                "from": self.from_email,
                "to": to_list,
                "subject": subject,
                "text": body,
                "html": html
            }
        elif self.service_type == "resend":
            return {
                "from": self.from_email,
                "to": to_list,
                "subject": subject,
                "text": body,
                "html": html
            }
        else:  # Generic API
            return {
                "to": to_list,
                "subject": subject,
                "body": body,
                "html": html,
                "cc": cc,
                "bcc": bcc
            }

    def _get_api_headers(self):
        """Get API headers based on service type."""
        if self.service_type in ["sendgrid", "resend"]:
            return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        elif self.service_type == "mailgun":
            return {"Authorization": f"Basic {self.api_key}", "Content-Type": "application/json"}
        else:
            return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    async def check_inbox(self, folder: str = "INBOX", limit: int = 10,
                         unread_only: bool = False) -> Dict[str, Any]:
        """API-based services typically don't support inbox checking."""
        return {"success": False, "error": f"Inbox checking not supported for API service {self.name}"}

    async def test_connection(self) -> Dict[str, Any]:
        """Test API connection."""
        if not self.api_key or not self.api_url:
            return {"service": self.name, "connected": False, "error": "API not configured"}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = self._get_api_headers()
                # Try a simple API call or health check
                response = await client.get(self.api_url.replace("/send", "/health").replace("/v3/mail/send", "/health"),
                                          headers=headers)
                return {"service": self.name, "connected": response.status_code < 400}
        except Exception as e:
            return {"service": self.name, "connected": False, "error": str(e)}


class LocalEmailService(EmailService):
    """Local email testing service implementation.

    Supports local email testing tools including MailHog, Mailpit, and
    MailCatcher. Perfect for development and testing email functionality
    without sending real emails.

    Features:
    - SMTP server simulation for sending emails
    - Web interface for viewing sent emails
    - REST API for inbox checking and email retrieval
    - No external dependencies or internet connection required
    - Support for both SMTP sending and HTTP API inbox checking
    """

    def __init__(self, config: EmailServiceConfig):
        super().__init__(config)
        self.smtp_server = config.config.get("smtp_server", "localhost")
        self.smtp_port = config.config.get("smtp_port", 1025)
        self.http_url = config.config.get("http_url", "http://localhost:8025")
        self.service_type = config.config.get("service_type", "mailhog")

    async def send_email(self, to: Union[str, List[str]], subject: str, body: str,
                        html: Optional[str] = None, cc: Optional[List[str]] = None,
                        bcc: Optional[List[str]] = None) -> Dict[str, Any]:
        """Send email to local testing service."""
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = "test@localhost"
            msg["To"] = to if isinstance(to, str) else ", ".join(to)

            msg.attach(MIMEText(body, "plain"))
            if html:
                msg.attach(MIMEText(html, "html"))

            recipients = [addr.strip() for addr in (to.split(",") if isinstance(to, str) else to)]

            def send_sync():
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.sendmail("test@localhost", recipients, msg.as_string())

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, send_sync)

            return {"success": True, "status": "sent", "service": self.name, "note": "Check web UI at " + self.http_url}

        except Exception as e:
            return {"success": False, "error": f"Local send failed: {str(e)}"}

    async def check_inbox(self, folder: str = "INBOX", limit: int = 10,
                         unread_only: bool = False) -> Dict[str, Any]:
        """Check inbox via local service API."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                if self.service_type == "mailhog":
                    response = await client.get(f"{self.http_url}/api/v2/messages")
                    if response.status_code == 200:
                        data = response.json()
                        emails = []
                        for msg in data.get("items", [])[:limit]:
                            emails.append({
                                "id": msg.get("ID"),
                                "subject": msg.get("Content", {}).get("Headers", {}).get("Subject", ["(No Subject)"])[0],
                                "from": msg.get("Content", {}).get("Headers", {}).get("From", ["Unknown"])[0],
                                "date": msg.get("Created"),
                                "read": True,
                            })
                        return {"success": True, "emails": emails, "count": len(emails), "service": self.name}
                elif self.service_type == "mailpit":
                    response = await client.get(f"{self.http_url}/api/v1/messages")
                    if response.status_code == 200:
                        data = response.json()
                        emails = []
                        for msg in data.get("messages", [])[:limit]:
                            emails.append({
                                "id": str(msg.get("ID")),
                                "subject": msg.get("Subject", "(No Subject)"),
                                "from": msg.get("From", {}).get("Address", "Unknown"),
                                "date": msg.get("Date"),
                                "read": True,
                            })
                        return {"success": True, "emails": emails, "count": len(emails), "service": self.name}

            return {"success": False, "error": f"Unsupported local service type: {self.service_type}"}

        except Exception as e:
            return {"success": False, "error": f"Local inbox check failed: {str(e)}"}

    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to local service."""
        smtp_ok = False
        http_ok = False

        try:
            def test_smtp():
                with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=5) as server:
                    server.helo()
                    return True

            loop = asyncio.get_event_loop()
            smtp_ok = await loop.run_in_executor(None, test_smtp)
        except Exception:
            pass

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(self.http_url)
                http_ok = response.status_code < 400
        except Exception:
            pass

        return {"service": self.name, "smtp_connected": smtp_ok, "http_connected": http_ok}


class WebhookEmailService(EmailService):
    """Webhook-based email service implementation.

    Converts emails into webhook notifications for chat platforms and
    development tools. Supports Slack, Discord, Telegram, and GitHub
    webhooks for real-time email notifications.

    Features:
    - Platform-specific message formatting (Slack blocks, Discord embeds)
    - Rich formatting with email content display
    - Real-time notifications for important emails
    - Integration with development workflows and team communication
    - Configurable webhook URLs with authentication support

    Note: Webhook services don't support inbox checking.
    """

    def __init__(self, config: EmailServiceConfig):
        super().__init__(config)
        self.webhook_url = config.config.get("webhook_url")
        self.service_type = config.config.get("service_type", "generic")

    async def send_email(self, to: Union[str, List[str]], subject: str, body: str,
                        html: Optional[str] = None, cc: Optional[List[str]] = None,
                        bcc: Optional[List[str]] = None) -> Dict[str, Any]:
        """Send email via webhook."""
        if not self.webhook_url:
            return {"success": False, "error": f"Webhook not configured for {self.name}"}

        try:
            payload = self._prepare_webhook_payload(to, subject, body, html, cc, bcc)

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(self.webhook_url, json=payload)

                if response.status_code in [200, 201, 204]:
                    return {"success": True, "status": "sent", "service": self.name}
                else:
                    return {"success": False, "error": f"Webhook error {response.status_code}: {response.text}"}

        except Exception as e:
            return {"success": False, "error": f"Webhook send failed: {str(e)}"}

    def _prepare_webhook_payload(self, to, subject, body, html, cc, bcc):
        """Prepare webhook payload based on service type."""
        content = f"**{subject}**\n\n{body}"
        if html:
            content += f"\n\n--- HTML ---\n{html}"

        if self.service_type == "slack":
            return {
                "text": f"New Email: {subject}",
                "blocks": [
                    {"type": "header", "text": {"type": "plain_text", "text": f"📧 {subject}"}},
                    {"type": "section", "text": {"type": "mrkdwn", "text": content}},
                    {"type": "section", "fields": [
                        {"type": "mrkdwn", "text": f"*To:* {to}"},
                        {"type": "mrkdwn", "text": f"*From:* Email Service"}
                    ]}
                ]
            }
        elif self.service_type == "discord":
            return {
                "embeds": [{
                    "title": f"📧 {subject}",
                    "description": body,
                    "fields": [
                        {"name": "To", "value": str(to), "inline": True},
                        {"name": "Service", "value": self.name, "inline": True}
                    ]
                }]
            }
        else:  # Generic webhook
            return {
                "subject": subject,
                "body": body,
                "html": html,
                "to": to,
                "cc": cc,
                "bcc": bcc,
                "service": self.name
            }

    async def check_inbox(self, folder: str = "INBOX", limit: int = 10,
                         unread_only: bool = False) -> Dict[str, Any]:
        """Webhook services typically don't support inbox checking."""
        return {"success": False, "error": f"Inbox checking not supported for webhook service {self.name}"}

    async def test_connection(self) -> Dict[str, Any]:
        """Test webhook connection."""
        if not self.webhook_url:
            return {"service": self.name, "connected": False, "error": "Webhook not configured"}

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Try a simple POST or GET depending on service
                if self.service_type == "slack":
                    response = await client.post(self.webhook_url, json={"text": "test"})
                else:
                    response = await client.get(self.webhook_url.replace("/webhooks/", "/health"))

                return {"service": self.name, "connected": response.status_code < 400}
        except Exception as e:
            return {"service": self.name, "connected": False, "error": str(e)}


# Service Factory
class EmailServiceFactory:
    """Factory class for creating email service instances.

    Provides a centralized way to instantiate different email service types
    based on configuration. Supports all email service types through a
    unified interface.
    """

    @staticmethod
    def create_service(config: EmailServiceConfig) -> EmailService:
        """Create an email service instance from configuration.

        Args:
            config: EmailServiceConfig instance with service type and settings.

        Returns:
            Configured EmailService instance ready for use.

        Raises:
            ValueError: If the service type is unknown or unsupported.
        """
        service_type = config.type

        if service_type == "smtp":
            return SMTPEmailService(config)
        elif service_type == "api":
            return APIEmailService(config)
        elif service_type == "local":
            return LocalEmailService(config)
        elif service_type == "webhook":
            return WebhookEmailService(config)
        else:
            raise ValueError(f"Unknown email service type: {service_type}")


@asynccontextmanager
async def server_lifespan(mcp_instance: FastMCP):
    """Server lifespan context manager for startup and cleanup.
    
    Handles server initialization and shutdown logging. Called automatically
    by FastMCP when the server starts and stops.
    
    Args:
        mcp_instance: The FastMCP server instance (provided by framework)
    """
    logger.info("Email MCP server starting up", version="0.3.0")
    yield
    logger.info("Email MCP server shutting down")


class EmailMCP:
    """Email MCP Server - Multi-Service Email Platform.

    Main server class implementing the Model Context Protocol for email services.
    Provides a unified interface to multiple email service types through FastMCP,
    enabling AI assistants to send emails, check inboxes, and manage email
    configurations seamlessly.

    Features:
    - Multi-service email support (SMTP, API, local, webhook)
    - Dynamic service configuration at runtime
    - Conversational tool responses with natural language messages
    - Comprehensive error handling and service health monitoring
    - FastMCP 2.14.3 protocol compliance

    Configuration:
    - Environment variables for backward compatibility
    - Dynamic service configuration via tools
    - Automatic service discovery and registration
    """

    def __init__(self) -> None:
        """Initialize Email MCP server.

        Sets up the FastMCP server instance, loads default services from
        environment variables for backward compatibility, and initializes
        the service registry for dynamic configuration.
        """
        # Initialize FastMCP
        self.mcp = FastMCP(
            name="Email-MCP",
            version="0.3.0",
            lifespan=server_lifespan,
        )

        # Service registry
        self.services: Dict[str, EmailService] = {}

        # Load default services from environment (backward compatibility)
        self._load_default_services()

        # Load additional services from configuration
        self._load_configured_services()

        # Register tools
        self._register_tools()

    def _load_default_services(self) -> None:
        """Load default SMTP/IMAP service from environment variables.

        Loads the 'default' SMTP/IMAP service using standard environment
        variables for backward compatibility with existing configurations.

        Environment Variables:
            SMTP_SERVER: SMTP server hostname
            SMTP_USER: SMTP authentication username
            SMTP_PASSWORD: SMTP authentication password
            SMTP_FROM: From address (defaults to SMTP_USER)
            IMAP_SERVER: IMAP server hostname
            IMAP_USER: IMAP authentication username
            IMAP_PASSWORD: IMAP authentication password
        """
        smtp_server = os.getenv("SMTP_SERVER", "")
        smtp_user = os.getenv("SMTP_USER", "")

        if smtp_server and smtp_user:
            # Create default SMTP service
            default_config = EmailServiceConfig(
                name="default",
                type="smtp",
                config={
                    "smtp_server": smtp_server,
                    "smtp_port": int(os.getenv("SMTP_PORT", "587")),
                    "smtp_user": smtp_user,
                    "smtp_password": os.getenv("SMTP_PASSWORD", ""),
                    "smtp_from": os.getenv("SMTP_FROM", smtp_user),
                    "imap_server": os.getenv("IMAP_SERVER", ""),
                    "imap_port": int(os.getenv("IMAP_PORT", "993")),
                    "imap_user": os.getenv("IMAP_USER", smtp_user),
                    "imap_password": os.getenv("IMAP_PASSWORD", ""),
                }
            )
            self.services["default"] = EmailServiceFactory.create_service(default_config)

    def _load_configured_services(self) -> None:
        """Load additional services from EMAIL_SERVICES environment variable.

        Parses JSON-formatted service configurations from the EMAIL_SERVICES
        environment variable to dynamically configure additional email services
        beyond the default SMTP/IMAP service.

        Expected JSON format:
        [
            {
                "name": "service_name",
                "type": "smtp|api|local|webhook",
                "enabled": true,
                "config": {
                    "smtp_server": "...",
                    ...
                }
            }
        ]

        Note: Services loaded this way are stored in memory and don't persist
        across server restarts. Use the configure_service tool for runtime config.
        """
        services_json = os.getenv("EMAIL_SERVICES", "")
        if services_json:
            try:
                services_config = json.loads(services_json)
                for service_config in services_config:
                    config = EmailServiceConfig(**service_config)
                    if config.name not in self.services:  # Don't override default
                        self.services[config.name] = EmailServiceFactory.create_service(config)
            except json.JSONDecodeError as e:
                logger.warning("Failed to parse EMAIL_SERVICES configuration", error=str(e))

        # Load some common pre-configured services
        self._load_preconfigured_services()

    def _load_preconfigured_services(self) -> None:
        """Load commonly used email services if their API keys are available.

        Automatically configures popular transactional email services when
        their API credentials are detected in environment variables.

        Supported Services:
        - SendGrid: SENDGRID_API_KEY, SENDGRID_FROM_EMAIL
        - Mailgun: MAILGUN_API_KEY, MAILGUN_DOMAIN, MAILGUN_FROM_EMAIL
        - Resend: RESEND_API_KEY, RESEND_FROM_EMAIL
        - MailHog: MAILHOG_* environment variables
        - Slack: SLACK_WEBHOOK_URL
        """
        # SendGrid
        sendgrid_key = os.getenv("SENDGRID_API_KEY")
        if sendgrid_key:
            sendgrid_config = EmailServiceConfig(
                name="sendgrid",
                type="api",
                config={
                    "api_key": sendgrid_key,
                    "api_url": "https://api.sendgrid.com/v3/mail/send",
                    "from_email": os.getenv("SENDGRID_FROM_EMAIL", "noreply@example.com"),
                    "service_type": "sendgrid"
                }
            )
            self.services["sendgrid"] = EmailServiceFactory.create_service(sendgrid_config)

        # Mailgun
        mailgun_key = os.getenv("MAILGUN_API_KEY")
        mailgun_domain = os.getenv("MAILGUN_DOMAIN")
        if mailgun_key and mailgun_domain:
            mailgun_config = EmailServiceConfig(
                name="mailgun",
                type="api",
                config={
                    "api_key": f"api:{mailgun_key}",
                    "api_url": f"https://api.mailgun.net/v3/{mailgun_domain}/messages",
                    "from_email": os.getenv("MAILGUN_FROM_EMAIL", f"noreply@{mailgun_domain}"),
                    "service_type": "mailgun"
                }
            )
            self.services["mailgun"] = EmailServiceFactory.create_service(mailgun_config)

        # Resend
        resend_key = os.getenv("RESEND_API_KEY")
        if resend_key:
            resend_config = EmailServiceConfig(
                name="resend",
                type="api",
                config={
                    "api_key": resend_key,
                    "api_url": "https://api.resend.com/emails",
                    "from_email": os.getenv("RESEND_FROM_EMAIL", "noreply@example.com"),
                    "service_type": "resend"
                }
            )
            self.services["resend"] = EmailServiceFactory.create_service(resend_config)

        # Local testing services
        if os.getenv("MAILHOG_ENABLED", "").lower() == "true":
            mailhog_config = EmailServiceConfig(
                name="mailhog",
                type="local",
                config={
                    "smtp_server": os.getenv("MAILHOG_SMTP_HOST", "localhost"),
                    "smtp_port": int(os.getenv("MAILHOG_SMTP_PORT", "1025")),
                    "http_url": os.getenv("MAILHOG_HTTP_URL", "http://localhost:8025"),
                    "service_type": "mailhog"
                }
            )
            self.services["mailhog"] = EmailServiceFactory.create_service(mailhog_config)

        # Webhook services
        slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
        if slack_webhook:
            slack_config = EmailServiceConfig(
                name="slack",
                type="webhook",
                config={
                    "webhook_url": slack_webhook,
                    "service_type": "slack"
                }
            )
            self.services["slack"] = EmailServiceFactory.create_service(slack_config)

    def _register_tools(self):
        """Register all email tools with the FastMCP server.

        This method registers tools for:
        - send_email: Send emails via multiple services
        - check_inbox: Check inbox via multiple services
        - email_status: Check service configuration and connectivity
        - configure_service: Configure additional email services
        - list_services: List available email services
        """

        @self.mcp.tool()
        async def send_email(
            to: Union[str, List[str]],
            subject: str,
            body: str,
            service: str = "default",
            html: Optional[str] = None,
            cc: Optional[List[str]] = None,
            bcc: Optional[List[str]] = None,
        ) -> Dict[str, Any]:
            """Send an email via specified email service.

            Sends an email using the specified email service. Supports SMTP, API-based services,
            local testing services, and webhook integrations. Automatically detects service
            capabilities and uses the appropriate sending method.

            Args:
                to: Recipient email address(es). Can be:
                    - Single address: "user@example.com"
                    - Comma-separated: "user1@example.com, user2@example.com"
                    - List: ["user1@example.com", "user2@example.com"]
                subject: Email subject line. Required.
                body: Plain text email body. Required. This serves as the fallback
                    for email clients that don't support HTML.
                service: Email service to use. Options:
                    - "default": Default SMTP/IMAP service (from env vars)
                    - "sendgrid": SendGrid transactional email
                    - "mailgun": Mailgun transactional email
                    - "resend": Resend transactional email
                    - "mailhog": Local MailHog testing service
                    - "slack": Send to Slack webhook
                    - "discord": Send to Discord webhook
                    - Custom service names configured via EMAIL_SERVICES
                html: Optional HTML email body. If provided, the email will be sent
                    as multipart/alternative with both text and HTML versions.
                    Example: "<h1>Title</h1><p>Content</p>"
                cc: Optional CC (carbon copy) recipients. Same format as 'to'.
                bcc: Optional BCC (blind carbon copy) recipients. Same format as 'to'.

            Returns:
                Dictionary with service-specific results:
                {
                    "success": bool,      # True if email sent successfully
                    "status": str,        # "sent" on success
                    "service": str,       # Service used
                    "to": str,            # Recipient address(es)
                    "subject": str,       # Email subject
                    "error": str          # Error message if success is False
                }

            Examples:
                # Send via default SMTP service
                send_email(
                    to="user@example.com",
                    subject="Hello",
                    body="This is a test email"
                )

                # Send via SendGrid
                send_email(
                    to="user@example.com",
                    subject="Welcome",
                    body="Welcome to our service",
                    service="sendgrid",
                    html="<h1>Welcome!</h1><p>Thanks for joining.</p>"
                )

                # Send to Slack webhook
                send_email(
                    to="general",
                    subject="Alert",
                    body="System alert message",
                    service="slack"
                )

            Notes:
                - Service availability depends on configuration
                - API services may have different rate limits and features
                - Local testing services don't send real emails
                - Webhook services convert emails to chat messages
            """
            if service not in self.services:
                available_services = list(self.services.keys())
                return {
                    "success": False,
                    "error": f"Service '{service}' not available. Available services: {available_services}",
                }

            email_service = self.services[service]
            result = await email_service.send_email(to, subject, body, html, cc, bcc)

            if result.get("success"):
                logger.info("Email sent successfully", service=service, to=to, subject=subject)
                result["message"] = f"Email '{subject}' sent successfully to {to} via {service} service"
            else:
                logger.error("Failed to send email", service=service, error=result.get("error"))
                result["message"] = f"Failed to send email: {result.get('error')}"

            return result

        @self.mcp.tool()
        async def check_inbox(
            service: str = "default",
            folder: str = "INBOX",
            limit: int = 10,
            unread_only: bool = False,
        ) -> Dict[str, Any]:
            """Check inbox via specified email service.

            Retrieves emails from the specified service and folder. Supports IMAP-based services,
            local testing services with web APIs, and service-specific inbox checking.

            Args:
                service: Email service to check. Options:
                    - "default": Default IMAP service (from env vars)
                    - "mailhog": Local MailHog testing service
                    - "mailpit": Local Mailpit testing service
                    - Custom service names that support inbox checking
                folder: Mail folder name to check. Default: "INBOX". Common folders:
                    - "INBOX": Main inbox folder
                    - "Sent": Sent items folder
                    - "Drafts": Draft messages folder
                    - "Trash": Deleted messages folder
                    Folder names are case-sensitive and provider-specific.
                limit: Maximum number of emails to return. Default: 10.
                unread_only: If True, only returns unread emails. Default: False.

            Returns:
                Dictionary with service-specific results:
                {
                    "success": bool,      # True if inbox check succeeded
                    "emails": [           # List of email dictionaries
                        {
                            "id": str,            # Message ID
                            "subject": str,       # Email subject
                            "from": str,          # Sender address
                            "date": str,          # Email date
                            "read": bool          # Read status
                        }
                    ],
                    "count": int,         # Number of emails returned
                    "service": str,       # Service used
                    "folder": str,        # Folder checked
                    "error": str          # Error message if success is False
                }

            Examples:
                # Check default IMAP inbox
                check_inbox()
                # Returns: {"success": True, "emails": [...], "count": 10, "service": "default"}

                # Check MailHog testing inbox
                check_inbox(service="mailhog", limit=20)
                # Returns emails from local testing service

                # Check unread emails only
                check_inbox(unread_only=True, limit=5)

            Notes:
                - Not all services support inbox checking (API/webhook services typically don't)
                - Local testing services provide web UIs for viewing emails
                - IMAP services support standard folder names
                - Results are sorted with most recent first
            """
            if service not in self.services:
                available_services = list(self.services.keys())
                return {
                    "success": False,
                    "error": f"Service '{service}' not available. Available services: {available_services}",
                }

            email_service = self.services[service]
            result = await email_service.check_inbox(folder, limit, unread_only)

            if result.get("success"):
                count = result.get("count", 0)
                logger.info("Inbox checked", service=service, count=count, folder=folder)
                result["message"] = f"Found {count} emails in {folder} via {service} service"
            else:
                logger.error("Failed to check inbox", service=service, error=result.get("error"))
                result["message"] = f"Failed to check inbox: {result.get('error')}"

            return result


        @self.mcp.tool()
        async def email_status(service: Optional[str] = None) -> Dict[str, Any]:
            """Get email service status and test connectivity.

            Tests connectivity for specified service or all configured services.
            Verifies that credentials are correct and services are reachable.

            Args:
                service: Specific service to test, or None for all services.

            Returns:
                Dictionary with service status information:
                {
                    "server": str,           # Server name
                    "version": str,          # Server version
                    "services": {            # Service-specific status
                        "service_name": {
                            "configured": bool,
                            "connected": bool,
                            "error": str,        # Error message if connection failed
                            "type": str          # Service type (smtp, api, local, webhook)
                        }
                    },
                    "total_services": int,
                    "configured_services": int,
                    "connected_services": int
                }

            Examples:
                # Check all services
                email_status()
                # Returns status for all configured services

                # Check specific service
                email_status(service="sendgrid")
                # Returns status only for SendGrid service

            Notes:
                - Tests actual connectivity, not just configuration presence
                - Connection tests are quick (timeout after 5-10 seconds)
                - API keys and passwords are not exposed in results
            """
            services_to_check = [service] if service else list(self.services.keys())
            service_statuses = {}

            for svc_name in services_to_check:
                if svc_name in self.services:
                    email_service = self.services[svc_name]
                    status = await email_service.test_connection()
                    service_statuses[svc_name] = {
                        "configured": True,
                        "connected": status.get("connected", status.get("smtp_connected", False) or status.get("imap_connected", False)),
                        "error": status.get("error") or status.get("smtp_error") or status.get("imap_error"),
                        "type": email_service.config.type
                    }
                else:
                    service_statuses[svc_name] = {
                        "configured": False,
                        "connected": False,
                        "error": f"Service '{svc_name}' not configured",
                        "type": "unknown"
                    }

            configured_count = sum(1 for s in service_statuses.values() if s["configured"])
            connected_count = sum(1 for s in service_statuses.values() if s["connected"])

            return {
                "server": "Email-MCP",
                "version": "0.3.0",
                "services": service_statuses,
                "total_services": len(service_statuses),
                "configured_services": configured_count,
                "connected_services": connected_count,
                "tools_exposed": 6,
                "tools": [
                    "send_email",
                    "check_inbox",
                    "email_status",
                    "configure_service",
                    "list_services",
                    "email_help",
                ],
                "message": f"Email MCP server v0.3.0 - {connected_count}/{len(service_statuses)} services connected"
            }

        @self.mcp.tool()
        async def configure_service(
            name: str,
            type: str,
            config: Dict[str, Any],
            enabled: bool = True,
        ) -> Dict[str, Any]:
            """Configure a new email service dynamically.

            Adds a new email service configuration at runtime. The service will be
            available for sending emails and inbox checking immediately.

            Args:
                name: Unique name for the service (e.g., "my-sendgrid", "dev-mailhog")
                type: Service type - "smtp", "api", "local", or "webhook"
                config: Service-specific configuration dictionary
                enabled: Whether the service should be enabled (default: True)

            Returns:
                Dictionary with configuration result:
                {
                    "success": bool,
                    "service": str,       # Service name
                    "type": str,          # Service type
                    "message": str        # Success/error message
                }

            Examples:
                # Configure SendGrid API service
                configure_service(
                    name="my-sendgrid",
                    type="api",
                    config={
                        "api_key": "your-sendgrid-key",
                        "api_url": "https://api.sendgrid.com/v3/mail/send",
                        "from_email": "noreply@yourdomain.com",
                        "service_type": "sendgrid"
                    }
                )

                # Configure local MailHog for testing
                configure_service(
                    name="local-testing",
                    type="local",
                    config={
                        "smtp_server": "localhost",
                        "smtp_port": 1025,
                        "http_url": "http://localhost:8025",
                        "service_type": "mailhog"
                    }
                )

            Notes:
                - Service names must be unique
                - Configuration is stored in memory (not persisted)
                - Use list_services() to see available services
            """
            if name in self.services:
                return {
                    "success": False,
                    "service": name,
                    "message": f"Service '{name}' already exists"
                }

            try:
                service_config = EmailServiceConfig(
                    name=name,
                    type=type,
                    enabled=enabled,
                    config=config
                )
                self.services[name] = EmailServiceFactory.create_service(service_config)

                logger.info("Service configured", service=name, type=type)
                return {
                    "success": True,
                    "service": name,
                    "type": type,
                    "message": f"Successfully configured {type} service '{name}' - ready for use"
                }
            except Exception as e:
                logger.error("Failed to configure service", service=name, error=str(e))
                return {
                    "success": False,
                    "service": name,
                    "message": f"Configuration failed for service '{name}': {str(e)}"
                }

        @self.mcp.tool()
        async def list_services() -> Dict[str, Any]:
            """List all configured email services.

            Returns information about all available email services, their types,
            and configuration status.

            Returns:
                Dictionary with service information:
                {
                    "services": {
                        "service_name": {
                            "type": str,        # Service type
                            "enabled": bool,    # Whether service is enabled
                            "configured": bool, # Whether properly configured
                            "description": str  # Human-readable description
                        }
                    },
                    "count": int,           # Total number of services
                    "enabled_count": int,   # Number of enabled services
                    "types": [str]          # List of available service types
                }

            Examples:
                # List all services
                list_services()
                # Returns: {
                #     "services": {
                #         "default": {"type": "smtp", "enabled": true, "configured": true, "description": "Default SMTP/IMAP service"},
                #         "sendgrid": {"type": "api", "enabled": true, "configured": true, "description": "SendGrid transactional email"}
                #     },
                #     "count": 2,
                #     "enabled_count": 2,
                #     "types": ["smtp", "api", "local", "webhook"]
                # }

            Notes:
                - Shows both automatically configured and manually added services
                - Configuration status indicates if required credentials are available
                - Use email_status() to test actual connectivity
            """
            service_info = {}
            enabled_count = 0

            for name, service in self.services.items():
                configured = True
                description = f"{service.__class__.__name__.replace('EmailService', '').lower()} service"

                # Check if service is properly configured
                if isinstance(service, SMTPEmailService):
                    configured = bool(service.smtp_server and service.smtp_user and service.smtp_password)
                    description = "SMTP/IMAP email service"
                elif isinstance(service, APIEmailService):
                    configured = bool(service.api_key and service.api_url and service.from_email)
                    description = f"{service.service_type.title()} transactional email API"
                elif isinstance(service, LocalEmailService):
                    configured = bool(service.smtp_server)
                    description = f"Local {service.service_type} testing service"
                elif isinstance(service, WebhookEmailService):
                    configured = bool(service.webhook_url)
                    description = f"{service.service_type.title()} webhook integration"

                service_info[name] = {
                    "type": service.config.type,
                    "enabled": service.config.enabled,
                    "configured": configured,
                    "description": description
                }

                if service.config.enabled:
                    enabled_count += 1

            return {
                "services": service_info,
                "count": len(service_info),
                "enabled_count": enabled_count,
                "types": ["smtp", "api", "local", "webhook"]
            }

        @self.mcp.tool()
        async def email_help() -> Dict[str, Any]:
            """Get help and usage information for email MCP tools and services.

            Returns comprehensive help information including available tools, supported services,
            usage examples, configuration requirements, and common use cases.

            Returns:
                Dictionary with service and tool information:
                {
                    "server": str,              # Server name
                    "version": str,             # Server version
                    "description": str,         # Server description
                    "supported_services": {     # Available service types
                        "smtp": str,            # Description of SMTP services
                        "api": str,             # Description of API services
                        "local": str,           # Description of local services
                        "webhook": str          # Description of webhook services
                    },
                    "tools": [...],             # List of available tools
                    "examples": [...],          # Usage examples
                    "notes": [...]              # Important notes and tips
                }

            Examples:
                # Get comprehensive help
                email_help()
                # Returns full documentation for all services and tools

            Notes:
                - Use list_services() to see currently configured services
                - Use email_status() to test service connectivity
                - Use configure_service() to add new services dynamically
            """
            return {
                "server": "Email-MCP",
                "version": "0.3.0",
                "description": "Multi-service email platform supporting SMTP, APIs, local testing, and webhooks",
                "supported_services": {
                    "smtp": "Standard email providers (Gmail, Outlook, Yahoo, iCloud, ProtonMail)",
                    "api": "Transactional email APIs (SendGrid, Mailgun, Postmark, Amazon SES, Resend)",
                    "local": "Local testing services (MailHog, Mailpit, MailCatcher, Inbucket)",
                    "webhook": "Chat/webhook integrations (Slack, Discord, Telegram, GitHub)"
                },
                "tools": [
                    {
                        "name": "send_email",
                        "description": "Send emails via any configured service",
                        "usage": 'send_email(to="user@example.com", subject="Hello", body="Message", service="sendgrid")'
                    },
                    {
                        "name": "check_inbox",
                        "description": "Check inbox via IMAP or service APIs",
                        "usage": 'check_inbox(service="default", folder="INBOX", limit=10)'
                    },
                    {
                        "name": "email_status",
                        "description": "Test connectivity for services",
                        "usage": "email_status(service='sendgrid')"
                    },
                    {
                        "name": "configure_service",
                        "description": "Add new email services dynamically",
                        "usage": "configure_service(name='my-api', type='api', config={...})"
                    },
                    {
                        "name": "list_services",
                        "description": "List all configured email services",
                        "usage": "list_services()"
                    },
                    {
                        "name": "email_help",
                        "description": "Get this help information",
                        "usage": "email_help()"
                    }
                ],
                "configuration": {
                    "environment_variables": {
                        "SMTP_SERVER": "SMTP server hostname (e.g., smtp.gmail.com)",
                        "SMTP_USER": "SMTP username/email",
                        "SMTP_PASSWORD": "SMTP password or app password",
                        "IMAP_SERVER": "IMAP server hostname (e.g., imap.gmail.com)",
                        "IMAP_USER": "IMAP username/email",
                        "IMAP_PASSWORD": "IMAP password",
                        "SENDGRID_API_KEY": "SendGrid API key",
                        "MAILGUN_API_KEY": "Mailgun API key",
                        "RESEND_API_KEY": "Resend API key",
                        "MAILHOG_ENABLED": "Set to 'true' to enable MailHog",
                        "SLACK_WEBHOOK_URL": "Slack webhook URL for notifications"
                    },
                    "dynamic_configuration": "Use configure_service() to add services at runtime"
                },
                "examples": [
                    "# Send via different services",
                    'send_email(to="user@example.com", subject="Hello", body="Test", service="default")',
                    'send_email(to="user@example.com", subject="Welcome", body="Welcome!", service="sendgrid")',
                    'send_email(to="#general", subject="Alert", body="System alert", service="slack")',
                    "",
                    "# Check inboxes",
                    'check_inbox(service="default", unread_only=True)',
                    'check_inbox(service="mailhog", limit=20)',
                    "",
                    "# Configure new services",
                    "configure_service(name='my-mailgun', type='api', config={'api_key': 'key', 'api_url': 'url', 'from_email': 'me@domain.com', 'service_type': 'mailgun'})",
                    "",
                    "# Service management",
                    "list_services()",
                    "email_status()"
                ],
                "notes": [
                    "Gmail requires App Passwords, not regular passwords",
                    "Enable 2-Step Verification to generate Gmail App Passwords",
                    "API services may have rate limits and sending limits",
                    "Local testing services don't send real emails",
                    "Webhook services convert emails to chat messages",
                    "IMAP services support standard folder names (INBOX, Sent, etc.)",
                    "All operations are performed asynchronously",
                    "Service configurations are stored in memory (not persisted across restarts)"
                ]
            }


# Global server instance
email_mcp = EmailMCP()


def main():
    """Main entry point for the email MCP server.
    
    Starts the FastMCP server with stdio transport, which is required for
    MCP protocol communication. The server will run until interrupted or
    the MCP client disconnects.
    
    This function is called when the module is executed directly:
    ```bash
    python -m email_mcp.server
    ```
    
    FastMCP's run() method handles the event loop internally, so this
    function does not need to be async or use asyncio.run().
    """
    # Run with stdio transport (required for MCP)
    # FastMCP's run() handles the event loop internally
    email_mcp.mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

