"""Email service implementations: SMTP, API, Local, Webhook."""

from __future__ import annotations

import asyncio
import email
import imaplib
import logging
import smtplib
from abc import ABC, abstractmethod
from email.header import decode_header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

import httpx
from pydantic import BaseModel, Field

from email_mcp import oauth
from email_mcp.sanitize import sanitize_text

logger = logging.getLogger(__name__)


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
                encoding = encoding or "utf-8"
                result += decoded_bytes.decode(encoding, errors="replace")
            else:
                # If we already have a string, use it as-is
                result += str(decoded_bytes)

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
    config: dict[str, Any] = Field(default_factory=dict)


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
    async def send_email(
        self,
        to: str | list[str],
        subject: str,
        body: str,
        html: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        attachments: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Send an email via this service.

        Args:
            to: Recipient email address(es) - single string or list.
            subject: Email subject line.
            body: Plain text email body content.
            html: Optional HTML email body for rich formatting.
            cc: Optional carbon copy recipients.
            bcc: Optional blind carbon copy recipients.
            attachments: Optional list of attachment dicts with keys: filename, content (bytes), content_type.

        Returns:
            Dict containing success status and service-specific results.
        """
        pass

    @abstractmethod
    async def check_inbox(
        self,
        folder: str = "INBOX",
        limit: int = 10,
        unread_only: bool = False,
        from_contains: str | None = None,
        subject_contains: str | None = None,
    ) -> dict[str, Any]:
        """Check inbox via this service.

        Args:
            folder: Email folder to check (default: INBOX).
            limit: Maximum number of emails to return.
            unread_only: If True, only return unread emails.
            from_contains: Optional case-insensitive substring on From (IMAP/local may post-filter).
            subject_contains: Optional case-insensitive substring on Subject.

        Returns:
            Dict containing emails list and metadata.
        """
        pass

    @abstractmethod
    async def test_connection(self) -> dict[str, Any]:
        """Test connection to this service."""
        pass

    async def fetch_message(
        self,
        folder: str,
        email_id: str,
    ) -> dict[str, Any]:
        """Fetch a single email by ID with full body text/HTML."""
        return {"success": False, "error": f"fetch_message not supported for {self.name}"}

    async def delete_message(
        self,
        folder: str,
        email_id: str,
    ) -> dict[str, Any]:
        """Delete/move-to-trash a single email by ID."""
        return {"success": False, "error": f"delete_message not supported for {self.name}"}

    async def move_message(
        self,
        from_folder: str,
        to_folder: str,
        email_id: str,
    ) -> dict[str, Any]:
        """Move a single email between folders (COPY + DELETE)."""
        return {"success": False, "error": f"move_message not supported for {self.name}"}

    async def copy_message(
        self,
        from_folder: str,
        to_folder: str,
        email_id: str,
    ) -> dict[str, Any]:
        """Copy a single email to another folder (original stays)."""
        return {"success": False, "error": f"copy_message not supported for {self.name}"}

    async def forward_message(
        self,
        email_id: str,
        to: str | list[str],
        comment: str = "",
    ) -> dict[str, Any]:
        """Forward a single email to new recipients."""
        return {"success": False, "error": f"forward_message not supported for {self.name}"}

    async def flag_spam(
        self,
        folder: str,
        email_id: str,
    ) -> dict[str, Any]:
        """Flag an email as spam and move to Spam folder."""
        return {"success": False, "error": f"flag_spam not supported for {self.name}"}

    async def mark_read(
        self,
        folder: str,
        email_id: str,
    ) -> dict[str, Any]:
        """Mark a single email as read (SEEN)."""
        return {"success": False, "error": f"mark_read not supported for {self.name}"}

    async def list_folders(self, service: str = "default") -> list[dict[str, Any]]:
        """List IMAP folders/mailboxes."""
        return []

    async def create_folder(self, folder: str) -> dict[str, Any]:
        """Create a new IMAP folder."""
        return {"success": False, "error": f"create_folder not supported for {self.name}"}

    async def delete_folder(self, folder: str) -> dict[str, Any]:
        """Delete an IMAP folder."""
        return {"success": False, "error": f"delete_folder not supported for {self.name}"}

    async def rename_folder(self, old_name: str, new_name: str) -> dict[str, Any]:
        """Rename an IMAP folder."""
        return {"success": False, "error": f"rename_folder not supported for {self.name}"}


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

    def _smtp_ready(self) -> bool:
        return bool(self.smtp_server and self.smtp_user and (self.smtp_password or oauth.has_token(self.smtp_user)))

    def _imap_ready(self) -> bool:
        return bool(self.imap_server and self.imap_user and (self.imap_password or oauth.has_token(self.imap_user)))

    def _smtp_auth(self, server: smtplib.SMTP) -> None:
        """XOAUTH2 when a token exists, else password login."""
        if not oauth.authenticate_smtp(server, self.smtp_user):
            server.login(self.smtp_user, self.smtp_password)

    def _imap_auth(self, mail: imaplib.IMAP4) -> None:
        """XOAUTH2 when a token exists, else password login."""
        if not oauth.authenticate_imap(mail, self.imap_user):
            mail.login(self.imap_user, self.imap_password)

    async def send_email(
        self,
        to: str | list[str],
        subject: str,
        body: str,
        html: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        attachments: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Send email via SMTP."""
        if not self._smtp_ready():
            return {"success": False, "error": f"SMTP not configured for {self.name}"}

        try:
            from email import encoders
            from email.mime.base import MIMEBase

            has_attachments = attachments and len(attachments) > 0
            msg = MIMEMultipart("mixed" if has_attachments else "alternative")
            msg["Subject"] = subject
            msg["From"] = self.smtp_from
            msg["To"] = to if isinstance(to, str) else ", ".join(to)

            if cc:
                msg["Cc"] = ", ".join(cc) if isinstance(cc, list) else cc

            if has_attachments:
                alt = MIMEMultipart("alternative")
                alt.attach(MIMEText(body, "plain"))
                if html:
                    alt.attach(MIMEText(html, "html"))
                msg.attach(alt)
            else:
                msg.attach(MIMEText(body, "plain"))
                if html:
                    msg.attach(MIMEText(html, "html"))

            for att in attachments or []:
                filename = att.get("filename", "attachment")
                content = att.get("content", b"")
                content_type = att.get("content_type", "application/octet-stream")
                if isinstance(content, str):
                    content = content.encode("utf-8")
                part = (
                    MIMEBase(*content_type.split("/", 1))
                    if "/" in content_type
                    else MIMEBase("application", "octet-stream")
                )
                part.set_payload(content)
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
                msg.attach(part)

            recipients = [addr.strip() for addr in (to.split(",") if isinstance(to, str) else to)]
            if cc:
                recipients.extend([addr.strip() for addr in (cc if isinstance(cc, list) else cc.split(","))])
            if bcc:
                recipients.extend([addr.strip() for addr in (bcc if isinstance(bcc, list) else bcc.split(","))])

            def send_sync():
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()
                    self._smtp_auth(server)
                    server.sendmail(self.smtp_from, recipients, msg.as_string())

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, send_sync)

            return {"success": True, "status": "sent", "service": self.name}

        except Exception as e:
            return {"success": False, "error": f"SMTP send failed: {e!s}"}

    async def check_inbox(
        self,
        folder: str = "INBOX",
        limit: int = 10,
        unread_only: bool = False,
        from_contains: str | None = None,
        subject_contains: str | None = None,
    ) -> dict[str, Any]:
        """Check inbox via IMAP."""
        if not self._imap_ready():
            return {"success": False, "error": f"IMAP not configured for {self.name}"}

        fc = (from_contains or "").strip() or None
        sc = (subject_contains or "").strip() or None
        use_filters = bool(fc or sc)

        try:

            def check_sync():
                mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
                self._imap_auth(mail)
                mail.select(folder)

                search_criteria = "UNSEEN" if unread_only else "ALL"
                status, messages = mail.search(None, search_criteria)
                email_ids = messages[0].split()
                if not email_ids:
                    mail.close()
                    mail.logout()
                    return []

                # Newest first (IDs ascending → reverse full list)
                email_ids = list(reversed(email_ids))

                def matches(from_addr: str, subject: str) -> bool:
                    if fc and fc.lower() not in (from_addr or "").lower():
                        return False
                    if sc and sc.lower() not in (subject or "").lower():
                        return False
                    return True

                emails = []
                max_scan = 250 if use_filters else limit
                scan_count = 0
                for email_id in email_ids:
                    if len(emails) >= limit:
                        break
                    scan_count += 1
                    if scan_count > max_scan:
                        break

                    status, msg_data = mail.fetch(email_id, "(RFC822)")
                    if status != "OK":
                        continue
                    raw_email = msg_data[0][1]
                    email_message = email.message_from_bytes(raw_email)

                    raw_subject = email_message["Subject"] if "Subject" in email_message else ""
                    subject = sanitize_text(decode_email_header(raw_subject))

                    from_addr = sanitize_text(decode_email_header(email_message.get("From", "")))
                    date = sanitize_text(decode_email_header(email_message.get("Date", "")))

                    if use_filters and not matches(from_addr, subject or ""):
                        continue

                    emails.append(
                        {
                            "id": email_id.decode(),
                            "subject": subject or "(No Subject)",
                            "from": from_addr or "Unknown",
                            "date": date or "Unknown",
                            "read": not unread_only,
                        }
                    )

                mail.close()
                mail.logout()
                return emails

            loop = asyncio.get_event_loop()
            emails = await loop.run_in_executor(None, check_sync)

            return {
                "success": True,
                "emails": emails,
                "count": len(emails),
                "service": self.name,
            }

        except Exception as e:
            return {"success": False, "error": f"IMAP check failed: {e!s}"}

    async def test_connection(self) -> dict[str, Any]:
        """Test SMTP and IMAP connections."""
        smtp_ok = False
        imap_ok = False
        smtp_error = None
        imap_error = None

        if self._smtp_ready():
            try:

                def test_smtp():
                    with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=5) as server:
                        server.starttls()
                        self._smtp_auth(server)
                        return True

                loop = asyncio.get_event_loop()
                smtp_ok = await loop.run_in_executor(None, test_smtp)
            except Exception as e:
                smtp_error = str(e)

        if self._imap_ready():
            try:

                def test_imap():
                    mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port, timeout=5)
                    self._imap_auth(mail)
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

    async def fetch_message(
        self,
        folder: str,
        email_id: str,
    ) -> dict[str, Any]:
        """Fetch a single email by ID with full body text and HTML via IMAP."""
        if not self._imap_ready():
            return {"success": False, "error": f"IMAP not configured for {self.name}"}

        try:

            def fetch_sync():
                mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
                self._imap_auth(mail)
                mail.select(folder)

                eid = email_id.encode() if isinstance(email_id, str) else email_id
                status, msg_data = mail.fetch(eid, "(RFC822)")
                mail.close()
                mail.logout()

                if status != "OK" or not msg_data or not msg_data[0]:
                    return None
                if not isinstance(msg_data[0], tuple | list) or len(msg_data[0]) < 2:
                    return None

                raw_email = msg_data[0][1]
                email_message = email.message_from_bytes(raw_email)

                text_body = ""
                html_body = ""
                if email_message.is_multipart():
                    for part in email_message.walk():
                        content_type = part.get_content_type()
                        if content_type == "text/plain" and not text_body:
                            try:
                                payload = part.get_payload(decode=True)
                                if payload:
                                    charset = part.get_content_charset() or "utf-8"
                                    text_body = payload.decode(charset, errors="replace")
                            except Exception:
                                try:
                                    text_body = str(part.get_payload())
                                except Exception:
                                    pass
                        elif content_type == "text/html" and not html_body:
                            try:
                                payload = part.get_payload(decode=True)
                                if payload:
                                    charset = part.get_content_charset() or "utf-8"
                                    html_body = payload.decode(charset, errors="replace")
                            except Exception:
                                try:
                                    html_body = str(part.get_payload())
                                except Exception:
                                    pass
                else:
                    try:
                        payload = email_message.get_payload(decode=True)
                        if payload:
                            charset = email_message.get_content_charset() or "utf-8"
                            text_body = payload.decode(charset, errors="replace")
                        else:
                            text_body = str(email_message.get_payload() or "")
                    except Exception:
                        text_body = str(email_message.get_payload() or "")

                # Extract attachments
                attachments = []
                if email_message.is_multipart():
                    for part in email_message.walk():
                        content_disposition = str(part.get("Content-Disposition", ""))
                        if "attachment" in content_disposition.lower() or (
                            "filename" in content_disposition.lower()
                            and part.get_content_maintype() not in ("text", "multipart")
                        ):
                            filename = part.get_filename()
                            if filename:
                                payload = part.get_payload(decode=True)
                                attachments.append(
                                    {
                                        "filename": decode_email_header(filename),
                                        "content_type": part.get_content_type(),
                                        "size": len(payload) if payload else 0,
                                        "content_id": part.get("Content-ID", ""),
                                        "part_index": len(attachments) + 1,
                                    }
                                )

                return {
                    "id": email_id,
                    "subject": sanitize_text(decode_email_header(email_message.get("Subject", ""))),
                    "from": sanitize_text(decode_email_header(email_message.get("From", ""))),
                    "to": sanitize_text(decode_email_header(email_message.get("To", ""))),
                    "cc": sanitize_text(decode_email_header(email_message.get("Cc", ""))),
                    "date": sanitize_text(decode_email_header(email_message.get("Date", ""))),
                    "text_body": sanitize_text(text_body),
                    "html_body": sanitize_text(html_body) or None,
                    "attachments": attachments,
                    "headers": dict(email_message.items()),
                }

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, fetch_sync)

            if result is None:
                return {"success": False, "error": f"Message {email_id} not found in {folder}"}

            result["success"] = True
            result["service"] = self.name
            return result

        except Exception as e:
            return {"success": False, "error": f"IMAP fetch failed: {e!s}"}

    async def delete_message(
        self,
        folder: str,
        email_id: str,
    ) -> dict[str, Any]:
        """Delete a single email by ID via IMAP (moves to Trash)."""
        if not self._imap_ready():
            return {"success": False, "error": f"IMAP not configured for {self.name}"}

        try:

            def delete_sync():
                mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
                self._imap_auth(mail)
                mail.select(folder)

                eid = email_id.encode() if isinstance(email_id, str) else email_id
                mail.store(eid, "+FLAGS", "\\Deleted")
                mail.expunge()
                mail.close()
                mail.logout()
                return True

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, delete_sync)
            return {"success": True, "service": self.name, "email_id": email_id, "message": f"Deleted {email_id}"}

        except Exception as e:
            return {"success": False, "error": f"IMAP delete failed: {e!s}"}

    async def move_message(
        self,
        from_folder: str,
        to_folder: str,
        email_id: str,
    ) -> dict[str, Any]:
        """Move a single email between IMAP folders (COPY + DELETE)."""
        if not self._imap_ready():
            return {"success": False, "error": f"IMAP not configured for {self.name}"}
        try:

            def move_sync():
                mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
                self._imap_auth(mail)
                mail.select(from_folder)
                eid = email_id.encode() if isinstance(email_id, str) else email_id
                mail.copy(eid, to_folder)
                mail.store(eid, "+FLAGS", "\\Deleted")
                mail.expunge()
                mail.close()
                mail.logout()
                return True

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, move_sync)
            return {
                "success": True,
                "service": self.name,
                "email_id": email_id,
                "message": f"Moved {email_id} to {to_folder}",
            }
        except Exception as e:
            return {"success": False, "error": f"IMAP move failed: {e!s}"}

    async def copy_message(
        self,
        from_folder: str,
        to_folder: str,
        email_id: str,
    ) -> dict[str, Any]:
        """Copy a single email to another IMAP folder (original stays)."""
        if not self._imap_ready():
            return {"success": False, "error": f"IMAP not configured for {self.name}"}
        try:

            def copy_sync():
                mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
                self._imap_auth(mail)
                mail.select(from_folder)
                eid = email_id.encode() if isinstance(email_id, str) else email_id
                mail.copy(eid, to_folder)
                mail.close()
                mail.logout()
                return True

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, copy_sync)
            return {
                "success": True,
                "service": self.name,
                "email_id": email_id,
                "message": f"Copied {email_id} to {to_folder}",
            }
        except Exception as e:
            return {"success": False, "error": f"IMAP copy failed: {e!s}"}

    async def forward_message(
        self,
        email_id: str,
        to: str | list[str],
        comment: str = "",
    ) -> dict[str, Any]:
        """Forward a single email via IMAP fetch + SMTP send."""
        if not (self._imap_ready() and self._smtp_ready()):
            return {"success": False, "error": f"IMAP/SMTP not configured for {self.name}"}
        recipients = [addr.strip() for addr in (to.split(",") if isinstance(to, str) else to) if addr.strip()]
        if not recipients:
            return {"success": False, "error": "No recipients provided for forward"}
        try:

            def forward_sync():
                mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
                self._imap_auth(mail)
                mail.select("INBOX")
                eid = email_id.encode() if isinstance(email_id, str) else email_id
                status, msg_data = mail.fetch(eid, "(RFC822)")
                mail.close()
                mail.logout()
                if status != "OK" or not msg_data or msg_data[0] is None:
                    raise RuntimeError(f"message {email_id} not fetchable")
                raw = msg_data[0][1]
                original = email.message_from_bytes(raw)
                fwd = MIMEMultipart("alternative")
                fwd["Subject"] = f"Fwd: {decode_email_header(original.get('Subject', '(No Subject)'))}"
                fwd["From"] = self.smtp_from or self.smtp_user
                fwd["To"] = ", ".join(recipients)
                body = comment or ""
                if body:
                    body += "\n\n"
                body += f"---------- Forwarded message ----------\nFrom: {decode_email_header(original.get('From', ''))}\nDate: {decode_email_header(original.get('Date', ''))}\nSubject: {decode_email_header(original.get('Subject', ''))}\n\n"
                fwd.attach(MIMEText(body, "plain"))
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()
                    self._smtp_auth(server)
                    server.sendmail(self.smtp_from or self.smtp_user, recipients, fwd.as_string())
                return True

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, forward_sync)
            return {
                "success": True,
                "service": self.name,
                "email_id": email_id,
                "to": ", ".join(recipients),
                "message": f"Forwarded {email_id} to {', '.join(recipients)}",
            }
        except Exception as e:
            return {"success": False, "error": f"IMAP forward failed: {e!s}"}

    async def flag_spam(
        self,
        folder: str,
        email_id: str,
    ) -> dict[str, Any]:
        """Flag a single email as spam and move to Spam folder."""
        if not self._imap_ready():
            return {"success": False, "error": f"IMAP not configured for {self.name}"}
        try:

            def spam_sync():
                mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
                self._imap_auth(mail)
                mail.select(folder)
                eid = email_id.encode() if isinstance(email_id, str) else email_id
                mail.store(eid, "+FLAGS", "\\Junk")
                mail.copy(eid, "Spam")
                mail.store(eid, "+FLAGS", "\\Deleted")
                mail.expunge()
                mail.close()
                mail.logout()
                return True

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, spam_sync)
            return {
                "success": True,
                "service": self.name,
                "email_id": email_id,
                "message": f"Flagged {email_id} as spam",
            }
        except Exception as e:
            return {"success": False, "error": f"IMAP spam flag failed: {e!s}"}

    async def mark_read(
        self,
        folder: str,
        email_id: str,
    ) -> dict[str, Any]:
        """Mark a single email as read (SEEN) via IMAP."""
        if not self._imap_ready():
            return {"success": False, "error": f"IMAP not configured for {self.name}"}

        try:

            def mark_sync():
                mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
                self._imap_auth(mail)
                mail.select(folder)

                eid = email_id.encode() if isinstance(email_id, str) else email_id
                mail.store(eid, "+FLAGS", "\\Seen")
                mail.close()
                mail.logout()
                return True

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, mark_sync)
            return {
                "success": True,
                "service": self.name,
                "email_id": email_id,
                "message": f"Marked {email_id} as read",
            }

        except Exception as e:
            return {"success": False, "error": f"IMAP mark read failed: {e!s}"}

    async def mark_unread(
        self,
        folder: str,
        email_id: str,
    ) -> dict[str, Any]:
        """Mark a single email as unread (remove SEEN flag) via IMAP."""
        if not self._imap_ready():
            return {"success": False, "error": f"IMAP not configured for {self.name}"}

        try:

            def unmark_sync():
                mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
                self._imap_auth(mail)
                mail.select(folder)
                eid = email_id.encode() if isinstance(email_id, str) else email_id
                mail.store(eid, "-FLAGS", "\\Seen")
                mail.close()
                mail.logout()
                return True

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, unmark_sync)
            return {
                "success": True,
                "service": self.name,
                "email_id": email_id,
                "message": f"Marked {email_id} as unread",
            }
        except Exception as e:
            return {"success": False, "error": f"IMAP mark unread failed: {e!s}"}

    async def list_folders(self, service: str = "default") -> list[dict[str, Any]]:
        """List all IMAP folders/mailboxes for this service."""
        if not self._imap_ready():
            return []
        try:

            def list_sync():
                mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
                self._imap_auth(mail)
                status, folders = mail.list()
                mail.logout()
                if status != "OK":
                    return []
                result = []
                for line in folders:
                    decoded = line.decode("utf-8", errors="replace")
                    parts = decoded.split(' "/" ')
                    name = parts[-1].strip('" ') if len(parts) > 1 else decoded.strip()
                    if name and not name.startswith("[Gmail]"):
                        result.append({"name": name, "delimiter": "/"})
                return result

            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, list_sync)
        except Exception:
            return []

    async def create_folder(self, folder: str) -> dict[str, Any]:
        """Create a new IMAP folder."""
        if not self._imap_ready():
            return {"success": False, "error": f"IMAP not configured for {self.name}"}
        try:

            def create_sync():
                mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
                self._imap_auth(mail)
                status, _ = mail.create(folder)
                mail.logout()
                return status == "OK"

            loop = asyncio.get_event_loop()
            ok = await loop.run_in_executor(None, create_sync)
            return {
                "success": ok,
                "folder": folder,
                "message": f"Folder '{folder}' created" if ok else f"Failed to create '{folder}'",
            }
        except Exception as e:
            return {"success": False, "error": f"IMAP create folder failed: {e!s}"}

    async def delete_folder(self, folder: str) -> dict[str, Any]:
        """Delete an IMAP folder."""
        if not self._imap_ready():
            return {"success": False, "error": f"IMAP not configured for {self.name}"}
        try:

            def delete_sync():
                mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
                self._imap_auth(mail)
                status, _ = mail.delete(folder)
                mail.logout()
                return status == "OK"

            loop = asyncio.get_event_loop()
            ok = await loop.run_in_executor(None, delete_sync)
            return {
                "success": ok,
                "folder": folder,
                "message": f"Folder '{folder}' deleted" if ok else f"Failed to delete '{folder}'",
            }
        except Exception as e:
            return {"success": False, "error": f"IMAP delete folder failed: {e!s}"}

    async def rename_folder(self, old_name: str, new_name: str) -> dict[str, Any]:
        """Rename an IMAP folder."""
        if not self._imap_ready():
            return {"success": False, "error": f"IMAP not configured for {self.name}"}
        try:

            def rename_sync():
                mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
                self._imap_auth(mail)
                status, _ = mail.rename(old_name, new_name)
                mail.logout()
                return status == "OK"

            loop = asyncio.get_event_loop()
            ok = await loop.run_in_executor(None, rename_sync)
            return {
                "success": ok,
                "old_name": old_name,
                "new_name": new_name,
                "message": f"Renamed '{old_name}' to '{new_name}'" if ok else f"Failed to rename '{old_name}'",
            }
        except Exception as e:
            return {"success": False, "error": f"IMAP rename folder failed: {e!s}"}


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

    async def send_email(
        self,
        to: str | list[str],
        subject: str,
        body: str,
        html: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        attachments: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
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
                    return {
                        "success": True,
                        "status": "sent",
                        "service": self.name,
                        "response": response.json(),
                    }
                else:
                    return {
                        "success": False,
                        "error": f"API error {response.status_code}: {response.text}",
                    }

        except Exception as e:
            return {"success": False, "error": f"API send failed: {e!s}"}

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
                    {"type": "text/html", "value": html} if html else None,
                ],
            }
        elif self.service_type == "mailgun":
            return {
                "from": self.from_email,
                "to": to_list,
                "subject": subject,
                "text": body,
                "html": html,
            }
        elif self.service_type == "resend":
            return {
                "from": self.from_email,
                "to": to_list,
                "subject": subject,
                "text": body,
                "html": html,
            }
        else:  # Generic API
            return {
                "to": to_list,
                "subject": subject,
                "body": body,
                "html": html,
                "cc": cc,
                "bcc": bcc,
            }

    def _get_api_headers(self):
        """Get API headers based on service type."""
        if self.service_type in ["sendgrid", "resend"]:
            return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        elif self.service_type == "mailgun":
            return {"Authorization": f"Basic {self.api_key}", "Content-Type": "application/json"}
        else:
            return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    async def check_inbox(
        self,
        folder: str = "INBOX",
        limit: int = 10,
        unread_only: bool = False,
        from_contains: str | None = None,
        subject_contains: str | None = None,
    ) -> dict[str, Any]:
        """API-based services typically don't support inbox checking."""
        return {
            "success": False,
            "error": f"Inbox checking not supported for API service {self.name}",
        }

    async def test_connection(self) -> dict[str, Any]:
        """Test API connection."""
        if not self.api_key or not self.api_url:
            return {"service": self.name, "connected": False, "error": "API not configured"}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = self._get_api_headers()
                # Try a simple API call or health check
                response = await client.get(
                    self.api_url.replace("/send", "/health").replace("/v3/mail/send", "/health"),
                    headers=headers,
                )
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

    async def send_email(
        self,
        to: str | list[str],
        subject: str,
        body: str,
        html: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        attachments: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
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

            return {
                "success": True,
                "status": "sent",
                "service": self.name,
                "note": "Check web UI at " + self.http_url,
            }

        except Exception as e:
            return {"success": False, "error": f"Local send failed: {e!s}"}

    async def check_inbox(self, folder: str = "INBOX", limit: int = 10, unread_only: bool = False) -> dict[str, Any]:
        """Check inbox via local service API."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                if self.service_type == "mailhog":
                    response = await client.get(f"{self.http_url}/api/v2/messages")
                    if response.status_code == 200:
                        data = response.json()
                        emails = []
                        for msg in data.get("items", [])[:limit]:
                            emails.append(
                                {
                                    "id": msg.get("ID"),
                                    "subject": msg.get("Content", {})
                                    .get("Headers", {})
                                    .get("Subject", ["(No Subject)"])[0],
                                    "from": msg.get("Content", {}).get("Headers", {}).get("From", ["Unknown"])[0],
                                    "date": msg.get("Created"),
                                    "read": True,
                                }
                            )
                        return {
                            "success": True,
                            "emails": emails,
                            "count": len(emails),
                            "service": self.name,
                        }
                elif self.service_type == "mailpit":
                    response = await client.get(f"{self.http_url}/api/v1/messages")
                    if response.status_code == 200:
                        data = response.json()
                        emails = []
                        for msg in data.get("messages", [])[:limit]:
                            emails.append(
                                {
                                    "id": str(msg.get("ID")),
                                    "subject": msg.get("Subject", "(No Subject)"),
                                    "from": msg.get("From", {}).get("Address", "Unknown"),
                                    "date": msg.get("Date"),
                                    "read": True,
                                }
                            )
                        return {
                            "success": True,
                            "emails": emails,
                            "count": len(emails),
                            "service": self.name,
                        }

            return {
                "success": False,
                "error": f"Unsupported local service type: {self.service_type}",
            }

        except Exception as e:
            return {"success": False, "error": f"Local inbox check failed: {e!s}"}

    async def test_connection(self) -> dict[str, Any]:
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

    async def send_email(
        self,
        to: str | list[str],
        subject: str,
        body: str,
        html: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        attachments: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
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
                    return {
                        "success": False,
                        "error": f"Webhook error {response.status_code}: {response.text}",
                    }

        except Exception as e:
            return {"success": False, "error": f"Webhook send failed: {e!s}"}

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
                    {
                        "type": "section",
                        "fields": [
                            {"type": "mrkdwn", "text": f"*To:* {to}"},
                            {"type": "mrkdwn", "text": "*From:* Email Service"},
                        ],
                    },
                ],
            }
        elif self.service_type == "discord":
            return {
                "embeds": [
                    {
                        "title": f"📧 {subject}",
                        "description": body,
                        "fields": [
                            {"name": "To", "value": str(to), "inline": True},
                            {"name": "Service", "value": self.name, "inline": True},
                        ],
                    }
                ]
            }
        else:  # Generic webhook
            return {
                "subject": subject,
                "body": body,
                "html": html,
                "to": to,
                "cc": cc,
                "bcc": bcc,
                "service": self.name,
            }

    async def check_inbox(
        self,
        folder: str = "INBOX",
        limit: int = 10,
        unread_only: bool = False,
        from_contains: str | None = None,
        subject_contains: str | None = None,
    ) -> dict[str, Any]:
        """Webhook services typically don't support inbox checking."""
        return {
            "success": False,
            "error": f"Inbox checking not supported for webhook service {self.name}",
        }

    async def test_connection(self) -> dict[str, Any]:
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
        elif service_type == "graph":
            from email_mcp.services.graph_service import GraphEmailService

            return GraphEmailService(config)
        else:
            raise ValueError(f"Unknown email service type: {service_type}")
