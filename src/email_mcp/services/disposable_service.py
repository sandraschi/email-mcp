"""Disposable (throwaway) email service via mail.tm (https://mail.tm).

Free, no API key, receive-only. One service instance == one throwaway address:
mint it with ``DisposableEmailService.mint()`` (or the ``throwaway`` quick
setup), read its inbox like any other service, delete the service when done.

Use cases: newsletter signups, trial accounts, testing signup flows, giving
out an address you can burn. NOT for sending -- mail.tm is receive-only, and
many sites block known disposable domains for registration.
"""

from __future__ import annotations

import secrets
from typing import Any

import httpx

from email_mcp.services.email_services import EmailService, EmailServiceConfig

MAILTM_BASE_URL = "https://api.mail.tm"
REQUEST_TIMEOUT_S = 20.0


def _random_password(length: int = 24) -> str:
    return secrets.token_urlsafe(length)[:length]


def _members(payload: Any) -> list[dict[str, Any]]:
    """mail.tm returns Hydra dicts for most collections but a bare JSON
    array for /domains — accept both shapes."""
    if isinstance(payload, list):
        return [m for m in payload if isinstance(m, dict)]
    if isinstance(payload, dict):
        members = payload.get("hydra:member", [])
        return [m for m in members if isinstance(m, dict)]
    return []


def _client(base_url: str, token: str | None = None) -> httpx.AsyncClient:
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return httpx.AsyncClient(base_url=base_url.rstrip("/"), headers=headers, timeout=REQUEST_TIMEOUT_S)


def _sender_name(sender: Any) -> str:
    """Format a mail.tm ``from``/``to`` party as ``Name <addr>`` or plain addr."""
    if isinstance(sender, dict):
        addr = sender.get("address", "")
        name = (sender.get("name") or "").strip()
        return f"{name} <{addr}>" if name else addr
    return str(sender or "")


class DisposableEmailService(EmailService):
    """Receive-only throwaway mailbox backed by mail.tm.

    Config keys:
        address: the full throwaway address (e.g. ``x7f2@mail.tm``).
        password: the account password (needed to re-login for a fresh token).
        token: JWT for API calls (minted at creation, refreshed on 401).
        base_url: API base (default ``https://api.mail.tm``).
    """

    def __init__(self, config: EmailServiceConfig):
        super().__init__(config)
        cfg = config.config or {}
        self.address: str = cfg.get("address", "")
        self.password: str = cfg.get("password", "")
        self.token: str = cfg.get("token", "")
        self.base_url: str = cfg.get("base_url", MAILTM_BASE_URL)

    # ── provisioning ────────────────────────────────────────────────

    @classmethod
    async def mint(cls, domain: str | None = None, prefix: str = "emailmcp") -> dict[str, Any]:
        """Create a fresh throwaway address and return its service config.

        Raises RuntimeError when mail.tm is unreachable or out of domains.
        """
        async with _client(MAILTM_BASE_URL) as client:
            domains_resp = await client.get("/domains")
            domains_resp.raise_for_status()
            members = _members(domains_resp.json())
            available = [d.get("domain", "") for d in members if d.get("domain")]
            if domain and domain not in available:
                raise RuntimeError(f"mail.tm domain {domain!r} not available (have: {available})")
            chosen = domain or (available[0] if available else "")
            if not chosen:
                raise RuntimeError("mail.tm returned no usable domains")
            address = f"{prefix}-{secrets.token_hex(4)}@{chosen}"
            password = _random_password()
            acc_resp = await client.post("/accounts", json={"address": address, "password": password})
            acc_resp.raise_for_status()
            tok_resp = await client.post("/token", json={"address": address, "password": password})
            tok_resp.raise_for_status()
            return {
                "address": address,
                "password": password,
                "token": tok_resp.json().get("token", ""),
                "base_url": MAILTM_BASE_URL,
            }

    async def _login(self) -> str:
        """Fetch a fresh JWT with the stored address + password."""
        if not self.address or not self.password:
            raise RuntimeError(f"throwaway service {self.name!r} has no address/password stored")
        async with _client(self.base_url) as client:
            resp = await client.post("/token", json={"address": self.address, "password": self.password})
            resp.raise_for_status()
            token = resp.json().get("token", "")
            if not token:
                raise RuntimeError("mail.tm login returned no token")
            self.token = token
            return token

    async def _get(self, path: str) -> httpx.Response:
        """GET with one transparent re-login on 401 (expired token)."""
        token = self.token or await self._login()
        async with _client(self.base_url, token) as client:
            resp = await client.get(path)
            if resp.status_code == 401:
                token = await self._login()
                async with _client(self.base_url, token) as retry_client:
                    resp = await retry_client.get(path)
            resp.raise_for_status()
            return resp

    async def _mutate(self, method: str, path: str, json: dict[str, Any] | None = None) -> httpx.Response:
        token = self.token or await self._login()
        async with _client(self.base_url, token) as client:
            resp = await client.request(method, path, json=json)
            if resp.status_code == 401:
                token = await self._login()
                async with _client(self.base_url, token) as retry_client:
                    resp = await retry_client.request(method, path, json=json)
            resp.raise_for_status()
            return resp

    # ── EmailService interface ──────────────────────────────────────

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
        return {
            "success": False,
            "error": "Throwaway addresses are receive-only (mail.tm cannot send). Use another service to send.",
        }

    async def check_inbox(
        self,
        folder: str = "INBOX",
        limit: int = 10,
        unread_only: bool = False,
        from_contains: str | None = None,
        subject_contains: str | None = None,
    ) -> dict[str, Any]:
        try:
            resp = await self._get("/messages")
            members = _members(resp.json())
            emails: list[dict[str, Any]] = []
            for m in members:
                seen = bool(m.get("seen", False))
                if unread_only and seen:
                    continue
                frm = _sender_name(m.get("from"))
                subj = m.get("subject", "")
                if from_contains and from_contains.lower() not in frm.lower():
                    continue
                if subject_contains and subject_contains.lower() not in subj.lower():
                    continue
                emails.append(
                    {
                        "id": m.get("id", ""),
                        "subject": subj,
                        "from": frm,
                        "date": m.get("createdAt", ""),
                        "isRead": seen,
                        "intro": m.get("intro", ""),
                    }
                )
                if len(emails) >= max(limit, 1):
                    break
            return {
                "success": True,
                "emails": emails,
                "count": len(emails),
                "service": self.name,
                "folder": "INBOX",
            }
        except Exception as e:
            return {"success": False, "error": f"throwaway inbox failed: {e!s}"}

    async def fetch_message(self, folder: str, email_id: str) -> dict[str, Any]:
        try:
            resp = await self._get(f"/messages/{email_id}")
            m = resp.json()
            to_addrs = [_sender_name(t) for t in m.get("to", []) or []]
            return {
                "success": True,
                "id": m.get("id", email_id),
                "subject": m.get("subject", ""),
                "from": _sender_name(m.get("from")),
                "to": to_addrs,
                "date": m.get("createdAt", ""),
                "text_body": m.get("text", "") or m.get("intro", ""),
                "html_body": m.get("html", ""),
                "service": self.name,
            }
        except Exception as e:
            return {"success": False, "error": f"throwaway fetch failed: {e!s}"}

    async def mark_read(self, folder: str, email_id: str) -> dict[str, Any]:
        try:
            await self._mutate("PATCH", f"/messages/{email_id}", {"seen": True})
            return {"success": True, "service": self.name, "email_id": email_id}
        except Exception as e:
            return {"success": False, "error": f"throwaway mark-read failed: {e!s}"}

    async def delete_message(self, folder: str, email_id: str) -> dict[str, Any]:
        try:
            await self._mutate("DELETE", f"/messages/{email_id}")
            return {"success": True, "service": self.name, "email_id": email_id}
        except Exception as e:
            return {"success": False, "error": f"throwaway delete failed: {e!s}"}

    async def list_folders(self, service: str = "default") -> list[dict[str, Any]]:
        return [{"id": "INBOX", "name": "INBOX"}]

    async def test_connection(self) -> dict[str, Any]:
        try:
            resp = await self._get("/me")
            me = resp.json()
            return {
                "success": True,
                "connected": True,
                "service": self.name,
                "address": me.get("address", self.address),
                "message": f"throwaway {me.get('address', self.address)} reachable",
            }
        except Exception as e:
            return {
                "success": False,
                "connected": False,
                "service": self.name,
                "error": f"throwaway unreachable: {e!s}",
            }
