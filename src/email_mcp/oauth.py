"""OAuth2 (XOAUTH2) support for Microsoft accounts via the device-code flow.

Personal Outlook.com/Hotmail accounts have SMTP/IMAP basic authentication
disabled (535 5.7.139 / AUTHENTICATE failed). The only supported path is OAuth2
with XOAUTH2 as the SASL mechanism. This module implements:

- Device-code flow (no redirect server needed): start -> user enters a code at
  microsoft.com/devicelogin -> poll until authorized -> tokens stored locally.
- Refresh-token rotation with transparent access-token refresh.
- XOAUTH2 auth-string construction for imaplib and smtplib.

Configuration (env):
- EMAIL_MCP_OAUTH_CLIENT_ID  (required; from your Azure app registration)
- EMAIL_MCP_OAUTH_SCOPE      (optional; default IMAP + SMTP + offline_access)
- EMAIL_MCP_OAUTH_TOKEN_FILE (optional; default data/oauth_tokens.json)

The token store is keyed by the account email and is NOT committed to git.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class OAuthUnavailable(Exception):
    """Raised when a token is missing, expired, or rejected by the provider."""


AUTHORITY = "https://login.microsoftonline.com/common/oauth2/v2.0"
DEVICE_CODE_URL = f"{AUTHORITY}/devicecode"
TOKEN_URL = f"{AUTHORITY}/token"
VERIFICATION_URI = "https://microsoft.com/devicelogin"

DEFAULT_SCOPE = "https://outlook.office.com/IMAP.AccessAsUser.All https://outlook.office.com/SMTP.Send offline_access"
GRAPH_SCOPE = "https://graph.microsoft.com/Mail.Read https://graph.microsoft.com/Mail.Send offline_access"

SCOPE_FAMILIES = {"exchange": DEFAULT_SCOPE, "graph": GRAPH_SCOPE}


def _family(scope: str) -> str:
    """Tokens are keyed per resource family: exchange (IMAP/SMTP) vs graph."""
    return "graph" if "graph.microsoft.com" in (scope or "") else "exchange"


def family_scope(family: str) -> str:
    """Resolve a scope family name ('exchange' | 'graph') to its scope string."""
    return SCOPE_FAMILIES.get(family, DEFAULT_SCOPE)


_lock = threading.RLock()


def client_id() -> str | None:
    return os.getenv("EMAIL_MCP_OAUTH_CLIENT_ID", "").strip() or None


def scope() -> str:
    return os.getenv("EMAIL_MCP_OAUTH_SCOPE", DEFAULT_SCOPE).strip()


def token_file() -> Path:
    path = os.getenv("EMAIL_MCP_OAUTH_TOKEN_FILE", "").strip()
    return Path(path) if path else Path(__file__).resolve().parent.parent.parent / "data" / "oauth_tokens.json"


@dataclass
class OAuthToken:
    """A stored OAuth2 token pair for one account."""

    account: str
    access_token: str
    refresh_token: str
    scope: str
    expires_at: float
    obtained_at: float = field(default_factory=time.time)


def _load_store() -> dict[str, dict[str, Any]]:
    path = token_file()
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - corrupt store should not crash
        logger.warning("oauth token store unreadable (%s): %s", path, exc)
    return {}


def _save_store(store: dict[str, dict[str, Any]]) -> None:
    path = token_file()
    with _lock:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(store, indent=2) + "\n", encoding="utf-8")


def save_token(token: OAuthToken) -> None:
    """Persist a token, keyed by account + resource family."""
    with _lock:
        store = _load_store()
        key = _token_key(token.account, token.scope)
        store[key] = asdict(token)
        # drop legacy plain-account key so lookups stay unambiguous
        store.pop(token.account.lower(), None)
        _save_store(store)


def _token_key(account: str, scope: str) -> str:
    return f"{account.lower()}|{_family(scope)}"


def get_token(account: str, scope: str = DEFAULT_SCOPE) -> OAuthToken | None:
    """Return a valid token for the account+family, refreshing when near expiry."""
    if not account:
        return None
    key = _token_key(account, scope)
    with _lock:
        store = _load_store()
        raw = store.get(key) or store.get(account.lower())
    if not raw:
        return None
    try:
        token = OAuthToken(**raw)
    except TypeError:
        return None

    if time.time() < token.expires_at - 120:
        return token

    cid = client_id()
    if not cid:
        return None
    refreshed = refresh_access_token(cid, token.refresh_token)
    if not refreshed:
        return None
    refreshed.account = token.account
    save_token(refreshed)
    return refreshed


def has_token(account: str, scope: str = DEFAULT_SCOPE) -> bool:
    if not account:
        return False
    with _lock:
        store = _load_store()
        return _token_key(account, scope) in store or account.lower() in store


def _post(url: str, data: dict[str, str], timeout: float = 60.0) -> dict[str, Any]:
    resp = httpx.post(url, data=data, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def start_device_flow(cid: str | None = None, scopes: str | None = None) -> dict[str, Any]:
    """Start a device-code flow. Returns user_code, verification_uri, device_code."""
    cid = cid or client_id()
    if not cid:
        return {"success": False, "error": "EMAIL_MCP_OAUTH_CLIENT_ID not configured"}
    try:
        data = _post(
            DEVICE_CODE_URL,
            {"client_id": cid, "scope": scopes or scope()},
        )
    except Exception as exc:
        return {"success": False, "error": f"device code request failed: {exc}"}
    return {
        "success": True,
        "device_code": data["device_code"],
        "user_code": data["user_code"],
        "verification_uri": data.get("verification_uri") or VERIFICATION_URI,
        "expires_in": data.get("expires_in", 900),
        "interval": data.get("interval", 5),
        "message": f"Go to {data.get('verification_uri') or VERIFICATION_URI} and enter code {data['user_code']}",
    }


def poll_device_flow(
    device_code: str,
    cid: str | None = None,
    scopes: str | None = None,
) -> dict[str, Any]:
    """Poll the device flow until the user authenticates.

    On success the token pair is persisted, keyed by the account email parsed
    from the id_token.
    """
    cid = cid or client_id()
    if not cid:
        return {"success": False, "status": "error", "error": "EMAIL_MCP_OAUTH_CLIENT_ID not configured"}
    try:
        data = _post(
            TOKEN_URL,
            {
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                "client_id": cid,
                "device_code": device_code,
                "scope": scopes or scope(),
            },
        )
    except httpx.HTTPStatusError as exc:
        try:
            err = exc.response.json()
        except Exception:
            err = {}
        error = err.get("error", "unknown")
        if error == "authorization_pending":
            return {"success": True, "status": "pending"}
        if error == "authorization_declined":
            return {"success": False, "status": "declined", "error": "User declined the request"}
        if error in ("expired_token", "bad_verification_code"):
            return {"success": False, "status": "expired", "error": error}
        return {"success": False, "status": "error", "error": error}
    except Exception as exc:
        return {"success": False, "status": "error", "error": f"poll failed: {exc}"}

    account = _account_from_id_token(data.get("id_token", ""))
    if not account:
        return {"success": False, "status": "error", "error": "Could not determine account from id_token"}
    token = OAuthToken(
        account=account,
        access_token=data["access_token"],
        refresh_token=data.get("refresh_token", ""),
        scope=data.get("scope", scopes or scope()),
        expires_at=time.time() + int(data.get("expires_in", 3600)),
    )
    save_token(token)
    logger.info("oauth token stored for %s", account)
    return {
        "success": True,
        "status": "authorized",
        "account": account,
        "expires_at": token.expires_at,
        "message": f"Authorized as {account}",
    }


def refresh_access_token(cid: str, refresh_token: str, scopes: str | None = None) -> OAuthToken | None:
    """Exchange a refresh token for a fresh access token."""
    try:
        data = _post(
            TOKEN_URL,
            {
                "grant_type": "refresh_token",
                "client_id": cid,
                "refresh_token": refresh_token,
                "scope": scopes or scope(),
            },
        )
    except Exception as exc:
        logger.warning("oauth refresh failed: %s", exc)
        return None
    return OAuthToken(
        account="",
        access_token=data["access_token"],
        refresh_token=data.get("refresh_token", refresh_token),
        scope=data.get("scope", scopes or scope()),
        expires_at=time.time() + int(data.get("expires_in", 3600)),
    )


def build_xoauth2(user: str, access_token: str) -> str:
    """Build the SASL XOAUTH2 string: user=<user>^Aauth=Bearer <token>^A^A."""
    return f"user={user}\x01auth=Bearer {access_token}\x01\x01"


def _account_from_id_token(id_token: str) -> str:
    """Extract the account email from the id_token JWT payload (no signature check)."""
    try:
        payload_b64 = id_token.split(".")[1]
        payload_b64 += "=" * (-len(payload_b64) % 4)
        claims = json.loads(base64.urlsafe_b64decode(payload_b64))
        for key in ("preferred_username", "email", "upn"):
            if claims.get(key):
                return str(claims[key])
    except Exception:
        pass
    return ""


def authenticate_imap(mail: Any, user: str) -> bool:
    """Authenticate an imaplib connection with XOAUTH2. Returns True on success.

    The caller should fall back to password login when this returns False.
    """
    token = get_token(user)
    if not token:
        return False
    auth_str = build_xoauth2(user, token.access_token).encode("utf-8")
    try:
        mail.authenticate("XOAUTH2", lambda _: auth_str)
        return True
    except Exception as exc:
        logger.warning("XOAUTH2 IMAP auth failed for %s: %s", user, exc)
        return False


def authenticate_smtp(server: Any, user: str) -> bool:
    """Authenticate an smtplib connection with XOAUTH2. Returns True on success."""
    token = get_token(user)
    if not token:
        return False
    auth_str = build_xoauth2(user, token.access_token)
    try:
        server.auth("XOAUTH2", lambda _: auth_str)
        return True
    except Exception as exc:
        logger.warning("XOAUTH2 SMTP auth failed for %s: %s", user, exc)
        return False
