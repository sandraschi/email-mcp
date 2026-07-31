"""Microsoft Graph email service (OAuth2 device-code flow).

Personal Outlook/Hotmail accounts have IMAP/SMTP basic auth disabled; the
robust path is the Microsoft Graph REST API with a Mail.Read/Mail.Send token
from the device-code flow (see email_mcp.oauth). This service implements the
standard EmailService interface against Graph, so all MCP tools (send, inbox,
search, folders, triage) work with service="graph" transparently.
"""

from __future__ import annotations

import base64
from typing import Any
from urllib.parse import quote

import httpx

from email_mcp import oauth
from email_mcp.sanitize import sanitize_text
from email_mcp.services.email_services import EmailService, EmailServiceConfig

GRAPH_BASE = "https://graph.microsoft.com/v1.0"

_WELL_KNOWN = {
    "inbox": "inbox",
    "sent": "sentitems",
    "drafts": "drafts",
    "trash": "deleteditems",
    "junk": "junkemail",
    "spam": "junkemail",
    "archive": "archive",
}


def _folder_id(folder: str) -> str:
    return _WELL_KNOWN.get(folder.strip().lower(), quote(folder.strip()))


def _recipients(addresses: list[str] | str | None) -> list[dict[str, Any]]:
    if not addresses:
        return []
    items = addresses if isinstance(addresses, list) else [a for a in str(addresses).split(",") if a.strip()]
    return [{"emailAddress": {"address": a.strip()}} for a in items if a.strip()]


def _body(message: dict[str, Any]) -> str:
    body = message.get("body", {})
    return sanitize_text(body.get("content", "") or "")


def _from_str(message: dict[str, Any]) -> str:
    frm = (message.get("from") or {}).get("emailAddress", {})
    name = frm.get("name") or ""
    addr = frm.get("address") or ""
    return f"{name} <{addr}>" if name else addr


def _addresses_str(recipients: list[dict[str, Any]] | None) -> str:
    if not recipients:
        return ""
    return ", ".join(r.get("emailAddress", {}).get("address", "") for r in recipients)


class GraphEmailService(EmailService):
    """Email service backed by the Microsoft Graph API (Mail.Read/Mail.Send)."""

    def __init__(self, config: EmailServiceConfig):
        super().__init__(config)
        self.user = config.config.get("user") or config.config.get("imap_user") or config.config.get("smtp_user") or ""

    def _ready(self) -> bool:
        return bool(self.user and oauth.has_token(self.user, oauth.GRAPH_SCOPE))

    def _token(self) -> str | None:
        token = oauth.get_token(self.user, oauth.GRAPH_SCOPE)
        return token.access_token if token else None

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> tuple[int, dict[str, Any]]:
        token = self._token()
        if not token:
            raise oauth.OAuthUnavailable(f"No Graph token for {self.user} — connect Outlook OAuth (Graph) first")
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }
        if json_body is not None:
            headers["Content-Type"] = "application/json"
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.request(
                method,
                f"{GRAPH_BASE}{path}",
                params=params,
                headers=headers,
                json=json_body,
            )
        if resp.status_code in (401, 403):
            raise oauth.OAuthUnavailable(
                f"Graph authorization failed (HTTP {resp.status_code}) for {self.user} — reconnect Outlook OAuth (Graph)"
            )
        if resp.status_code >= 400:
            raise RuntimeError(f"Graph {method} {path} -> HTTP {resp.status_code}: {resp.text[:300]}")
        if resp.status_code == 204:
            return 204, {}
        return resp.status_code, resp.json()

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
        """Send via POST /me/sendMail."""
        if not self._ready():
            return {"success": False, "error": f"Graph not authorized for {self.name}"}
        try:
            message: dict[str, Any] = {
                "subject": subject,
                "body": {
                    "contentType": "html" if html else "text",
                    "content": html or body,
                },
                "toRecipients": _recipients(to),
            }
            if cc:
                message["ccRecipients"] = _recipients(cc)
            if bcc:
                message["bccRecipients"] = _recipients(bcc)
            if attachments:
                message["attachments"] = []
                for att in attachments or []:
                    content = att.get("content", b"")
                    if isinstance(content, str):
                        content = content.encode("utf-8")
                    message["attachments"].append(
                        {
                            "@odata.type": "#microsoft.graph.fileAttachment",
                            "name": att.get("filename", "attachment"),
                            "contentType": att.get("content_type", "application/octet-stream"),
                            "contentBytes": base64.b64encode(content).decode(),
                        }
                    )
            payload = {"message": message, "saveToSentItems": True}
            _, _ = await self._request("POST", "/me/sendMail", json_body=payload)
            return {
                "success": True,
                "status": "sent",
                "service": self.name,
                "message": f"Email '{subject}' sent to {to} via Graph",
            }
        except oauth.OAuthUnavailable as exc:
            return {"success": False, "error": str(exc)}
        except Exception as exc:
            return {"success": False, "error": f"Graph send failed: {exc}"}

    async def check_inbox(
        self,
        folder: str = "INBOX",
        limit: int = 10,
        unread_only: bool = False,
        from_contains: str | None = None,
        subject_contains: str | None = None,
    ) -> dict[str, Any]:
        """List messages from a folder."""
        if not self._ready():
            return {"success": False, "error": f"Graph not authorized for {self.name}"}
        try:
            params = {
                "$top": str(min(limit, 50)),
                "$orderby": "receivedDateTime desc",
                "$select": "id,subject,from,receivedDateTime,isRead",
            }
            if unread_only:
                params["$filter"] = "isRead eq false"
            _, data = await self._request("GET", f"/me/mailFolders/{_folder_id(folder)}/messages", params=params)
            emails = []
            for item in data.get("value", []):
                frm = _from_str(item)
                subject = sanitize_text(item.get("subject", ""))
                if from_contains and from_contains.lower() not in frm.lower():
                    continue
                if subject_contains and subject_contains.lower() not in subject.lower():
                    continue
                emails.append(
                    {
                        "id": item.get("id", ""),
                        "subject": subject or "(No Subject)",
                        "from": frm or "Unknown",
                        "date": item.get("receivedDateTime") or "Unknown",
                        "read": not item.get("isRead", False),
                    }
                )
                if len(emails) >= limit:
                    break
            return {
                "success": True,
                "emails": emails,
                "count": len(emails),
                "service": self.name,
                "folder": folder,
                "message": f"Found {len(emails)} emails in {folder} via Graph",
            }
        except oauth.OAuthUnavailable as exc:
            return {"success": False, "error": str(exc)}
        except Exception as exc:
            return {"success": False, "error": f"Graph inbox check failed: {exc}"}

    async def fetch_message(self, folder: str, email_id: str) -> dict[str, Any]:
        """Fetch a single message with body."""
        if not self._ready():
            return {"success": False, "error": f"Graph not authorized for {self.name}"}
        try:
            _, data = await self._request(
                "GET",
                f"/me/messages/{quote(email_id)}",
                params={"$select": "id,subject,from,toRecipients,ccRecipients,receivedDateTime,body,isRead"},
            )
            return {
                "success": True,
                "id": data.get("id", email_id),
                "subject": sanitize_text(data.get("subject", "")),
                "from": _from_str(data),
                "to": _addresses_str(data.get("toRecipients")),
                "cc": _addresses_str(data.get("ccRecipients")),
                "date": data.get("receivedDateTime") or "",
                "text_body": _body(data),
                "html_body": _body(data) if data.get("body", {}).get("contentType") == "html" else None,
                "service": self.name,
                "message": f"Fetched message {email_id}",
            }
        except oauth.OAuthUnavailable as exc:
            return {"success": False, "error": str(exc)}
        except Exception as exc:
            return {"success": False, "error": f"Graph fetch failed: {exc}"}

    async def delete_message(self, folder: str, email_id: str) -> dict[str, Any]:
        """Delete (soft) a message — Graph moves it to deleteditems."""
        if not self._ready():
            return {"success": False, "error": f"Graph not authorized for {self.name}"}
        try:
            await self._request("DELETE", f"/me/messages/{quote(email_id)}")
            return {
                "success": True,
                "service": self.name,
                "email_id": email_id,
                "message": f"Deleted message {email_id}",
            }
        except Exception as exc:
            return {"success": False, "error": f"Graph delete failed: {exc}"}

    async def move_message(self, from_folder: str, to_folder: str, email_id: str) -> dict[str, Any]:
        """Move a message to another folder."""
        if not self._ready():
            return {"success": False, "error": f"Graph not authorized for {self.name}"}
        try:
            await self._request(
                "POST",
                f"/me/messages/{quote(email_id)}/move",
                json_body={"destinationId": _folder_id(to_folder)},
            )
            return {
                "success": True,
                "service": self.name,
                "email_id": email_id,
                "to_folder": to_folder,
                "message": f"Moved message {email_id} to {to_folder}",
            }
        except Exception as exc:
            return {"success": False, "error": f"Graph move failed: {exc}"}

    async def flag_spam(self, folder: str, email_id: str) -> dict[str, Any]:
        """Flag as spam: move to Junk + add Spam category."""
        if not self._ready():
            return {"success": False, "error": f"Graph not authorized for {self.name}"}
        try:
            await self._request(
                "POST",
                f"/me/messages/{quote(email_id)}/move",
                json_body={"destinationId": "junkemail"},
            )
            return {
                "success": True,
                "service": self.name,
                "email_id": email_id,
                "message": f"Flagged message {email_id} as spam",
            }
        except Exception as exc:
            return {"success": False, "error": f"Graph flag_spam failed: {exc}"}

    async def _set_read(self, email_id: str, read: bool) -> dict[str, Any]:
        if not self._ready():
            return {"success": False, "error": f"Graph not authorized for {self.name}"}
        try:
            await self._request("PATCH", f"/me/messages/{quote(email_id)}", json_body={"isRead": read})
            return {
                "success": True,
                "service": self.name,
                "email_id": email_id,
                "message": f"Marked message {email_id} {'read' if read else 'unread'}",
            }
        except Exception as exc:
            return {"success": False, "error": f"Graph mark failed: {exc}"}

    async def mark_read(self, folder: str, email_id: str) -> dict[str, Any]:
        return await self._set_read(email_id, True)

    async def mark_unread(self, folder: str, email_id: str) -> dict[str, Any]:
        return await self._set_read(email_id, False)

    async def list_folders(self, service: str = "default") -> list[dict[str, Any]]:
        if not self._ready():
            return []
        try:
            _, data = await self._request("GET", "/me/mailFolders", params={"$select": "id,displayName"})
            return [{"name": f.get("displayName", ""), "delimiter": "/"} for f in data.get("value", [])]
        except Exception:
            return []

    async def create_folder(self, folder: str) -> dict[str, Any]:
        if not self._ready():
            return {"success": False, "error": f"Graph not authorized for {self.name}"}
        try:
            await self._request("POST", "/me/mailFolders", json_body={"displayName": folder})
            return {"success": True, "folder": folder, "message": f"Created folder {folder}"}
        except Exception as exc:
            return {"success": False, "error": f"Graph create_folder failed: {exc}"}

    async def delete_folder(self, folder: str) -> dict[str, Any]:
        if not self._ready():
            return {"success": False, "error": f"Graph not authorized for {self.name}"}
        try:
            await self._request("DELETE", f"/me/mailFolders/{_folder_id(folder)}")
            return {"success": True, "folder": folder, "message": f"Deleted folder {folder}"}
        except Exception as exc:
            return {"success": False, "error": f"Graph delete_folder failed: {exc}"}

    async def rename_folder(self, old_name: str, new_name: str) -> dict[str, Any]:
        if not self._ready():
            return {"success": False, "error": f"Graph not authorized for {self.name}"}
        try:
            await self._request(
                "PATCH",
                f"/me/mailFolders/{_folder_id(old_name)}",
                json_body={"displayName": new_name},
            )
            return {
                "success": True,
                "old_name": old_name,
                "new_name": new_name,
                "message": f"Renamed folder {old_name} -> {new_name}",
            }
        except Exception as exc:
            return {"success": False, "error": f"Graph rename_folder failed: {exc}"}

    async def search(self, query: str, folder: str = "INBOX", limit: int = 20) -> dict[str, Any]:
        """Search messages via Graph $search (subject/from/body keywords)."""
        if not self._ready():
            return {"success": False, "error": f"Graph not authorized for {self.name}"}
        try:
            params = {
                "$search": f'"{query}"',
                "$top": str(min(limit, 50)),
                "$select": "id,subject,from,receivedDateTime,isRead",
            }
            if folder and folder.strip().lower() not in ("inbox", ""):
                params["$search"] = f'"{query}" AND folder:{_folder_id(folder)}'
            _, data = await self._request("GET", "/me/messages", params=params)
            emails = [
                {
                    "id": item.get("id", ""),
                    "subject": sanitize_text(item.get("subject", "")) or "(No Subject)",
                    "from": _from_str(item) or "Unknown",
                    "date": item.get("receivedDateTime") or "Unknown",
                }
                for item in data.get("value", [])
            ]
            return {
                "success": True,
                "emails": emails,
                "count": len(emails),
                "service": self.name,
                "folder": folder,
                "query": query,
                "message": f"Found {len(emails)} matches via Graph",
            }
        except oauth.OAuthUnavailable as exc:
            return {"success": False, "error": str(exc)}
        except Exception as exc:
            return {"success": False, "error": f"Graph search failed: {exc}"}

    async def test_connection(self) -> dict[str, Any]:
        """Probe Graph connectivity."""
        smtp_ok = False
        imap_ok = False
        smtp_error = None
        imap_error = None
        try:
            await self._request("GET", "/me/mailFolders/inbox")
            imap_ok = True
        except Exception as exc:
            imap_error = str(exc)
        return {
            "service": self.name,
            "smtp_connected": smtp_ok,
            "imap_connected": imap_ok,
            "smtp_error": smtp_error,
            "imap_error": imap_error,
            "type": "graph",
        }
