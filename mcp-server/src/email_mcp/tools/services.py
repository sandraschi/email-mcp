"""
Email Service Implementations

Concrete implementations of email services for different providers and protocols.
"""

import asyncio
import email
import imaplib
import smtplib
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional, Union

import httpx

from .models import EmailServiceConfig


class EmailService(ABC):
    """Abstract base class for email services."""

    def __init__(self, config: EmailServiceConfig):
        self.config = config
        self.name = config.name

    @abstractmethod
    async def send_email(self, to: Union[str, List[str]], subject: str, body: str,
                        html: Optional[str] = None, cc: Optional[List[str]] = None,
                        bcc: Optional[List[str]] = None) -> Dict[str, Any]:
        """Send an email via this service."""
        pass

    @abstractmethod
    async def check_inbox(self, folder: str = "INBOX", limit: int = 10,
                         unread_only: bool = False) -> Dict[str, Any]:
        """Check inbox via this service."""
        pass

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to this service."""
        pass


class SMTPEmailService(EmailService):
    """SMTP-based email service (Gmail, Outlook, Yahoo, etc.)."""

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

                        emails.append({
                            "id": email_id.decode(),
                            "subject": email_message["Subject"] or "(No Subject)",
                            "from": email_message["From"] or "Unknown",
                            "date": email_message["Date"] or "Unknown",
                            "read": not unread_only,
                        })

                mail.close()
                mail.logout()
                return emails

            loop = asyncio.get_event_loop()
            emails = await loop.run_in_executor(None, check_sync)

            return {"success": True, "emails": emails, "count": len(emails), "service": self.name}

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
    """API-based email service (SendGrid, Mailgun, Resend, etc.)."""

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
    """Local testing email service (MailHog, Mailpit, etc.)."""

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
    """Webhook-based email service (Slack, Discord, Telegram, etc.)."""

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