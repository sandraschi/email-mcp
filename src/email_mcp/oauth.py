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

DEFAULT_SCOPE = "openid profile email https://outlook.office.com/IMAP.AccessAsUser.All https://outlook.office.com/SMTP.Send offline_access"
GRAPH_SCOPE = (
    "openid profile email https://graph.microsoft.com/Mail.Read https://graph.microsoft.com/Mail.Send offline_access"
)

SCOPE_FAMILIES = {"exchange": DEFAULT_SCOPE, "graph": GRAPH_SCOPE}


def _family(scope: str) -> str:
    """Tokens are keyed per resource family: exchange (IMAP/SMTP) vs graph."""
    return "graph" if "graph.microsoft.com" in (scope or "") else "exchange"


def family_scope(family: str) -> str:
    """Resolve a scope family name ('exchange' | 'graph') to its scope string."""
    return SCOPE_FAMILIES.get(family, DEFAULT_SCOPE)


_lock = threading.RLock()

# Cooldown so a dead refresh token is not hammered on every poll cycle.
# (account, family) -> unix ts until which refreshes are skipped.
_refresh_fail_until: dict[tuple[str, str], float] = {}
_REFRESH_FAIL_COOLDOWN = 120.0  # seconds

# Refresh errors that mean the refresh token is permanently dead (revoked,
# expired due to inactivity, or the client id changed). These trigger the
# auto-recovery device flow instead of a retry loop.
_PERMANENT_DEAD_CODES = {"invalid_grant", "invalid_client", "unauthorized_client"}

# Auto-recovery state: when a refresh token dies, the guardian starts a new
# device flow on its own, polls it, and swaps in the fresh token. The user
# only has to type the one-time code at microsoft.com/devicelogin.
_DEAD: dict[tuple[str, str], float] = {}  # (account, family) -> when marked dead
_AUTO_FLOW: dict[str, Any] | None = None  # pending auto-recovery device flow
_GUARDIAN_THREAD: threading.Thread | None = None
_GUARDIAN_INTERVAL = 30.0  # seconds between guardian ticks
_WARM_MARGIN = 300.0  # seconds before expiry at which the guardian refreshes


def client_id() -> str | None:
    return os.getenv("EMAIL_MCP_OAUTH_CLIENT_ID", "").strip() or None


def scope() -> str:
    return os.getenv("EMAIL_MCP_OAUTH_SCOPE", DEFAULT_SCOPE).strip()


def _tauri_appdata_dir() -> Path | None:
    r"""%LOCALAPPDATA%\{identifier} when running inside the Tauri wrapper."""
    base = os.getenv("LOCALAPPDATA", "")
    if base and os.getenv("EMAIL_MCP_TAURI", "").lower() in ("1", "true", "yes"):
        return Path(base) / "ai.fleet.email-mcp"
    return None


def token_file() -> Path:
    path = os.getenv("EMAIL_MCP_OAUTH_TOKEN_FILE", "").strip()
    if path:
        return Path(path)
    appdata = _tauri_appdata_dir()
    if appdata is not None:
        return appdata / "oauth_tokens.json"
    return Path(__file__).resolve().parent.parent.parent / "data" / "oauth_tokens.json"


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
    fam = _family(token.scope)
    if _dead_key(token.account, fam) in _DEAD:
        # Refresh token is known-dead: serve the access token until it truly
        # expires (degraded mode), the guardian handles the re-auth flow.
        return token if time.time() < token.expires_at else None
    if _refresh_fail_until.get((token.account.lower(), fam), 0.0) > time.time():
        return token if time.time() < token.expires_at else None
    refreshed, err_code = refresh_access_token(cid, token.refresh_token, scopes=token.scope)
    if refreshed:
        refreshed.account = token.account
        save_token(refreshed)
        return refreshed
    if err_code in _PERMANENT_DEAD_CODES:
        mark_token_dead(token.account, fam)
    else:
        _refresh_fail_until[(token.account.lower(), fam)] = time.time() + _REFRESH_FAIL_COOLDOWN
    # degraded mode: keep serving the current access token until it expires
    return token if time.time() < token.expires_at else None


def has_token(account: str, scope: str = DEFAULT_SCOPE) -> bool:
    if not account:
        return False
    with _lock:
        store = _load_store()
        return _token_key(account, scope) in store or account.lower() in store


def graph_account() -> str | None:
    """Return the account that holds a graph-family token, if any.

    Used by services that don't know the account yet (e.g. the installed
    desktop app before OAuth consent).
    """
    with _lock:
        store = _load_store()
        for key in store:
            if key.endswith("|graph"):
                return key.rsplit("|", 1)[0]
    return None


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

    account = _account_from_id_token(data.get("id_token", "")) or _account_from_id_token(data.get("access_token", ""))
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


def refresh_access_token(cid: str, refresh_token: str, scopes: str | None = None) -> tuple[OAuthToken | None, str]:
    """Exchange a refresh token for a fresh access token.

    Returns (token, error_code): error_code is "" on success, a permanent
    error name ("invalid_grant", "invalid_client", ...) when the refresh
    token is dead, or "network" for transient failures.
    """
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
    except httpx.HTTPStatusError as exc:
        err_code = ""
        try:
            err = exc.response.json()
            err_code = err.get("error", "")
            detail = err.get("error_description") or err_code
        except Exception:
            detail = ""
        logger.warning("oauth refresh failed: %s - %s", exc.response.status_code, detail)
        return None, err_code
    except Exception as exc:
        logger.warning("oauth refresh failed: %s", exc)
        return None, "network"
    return (
        OAuthToken(
            account="",
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token", refresh_token),
            scope=data.get("scope", scopes or scope()),
            expires_at=time.time() + int(data.get("expires_in", 3600)),
        ),
        "",
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


# ── Auto-recovery guardian ─────────────────────────────────────────────────
# Background daemon: keeps access tokens warm (proactive refresh, which also
# resets Microsoft's inactivity clock on the refresh token) and, when a
# refresh token dies, automatically starts a new device-code flow, polls it
# until the user enters the code, and stores the fresh token. The server
# never needs manual reconnection - the user only types the one-time code.


def _dead_key(account: str, family: str) -> tuple[str, str]:
    return (account.lower(), family)


def mark_token_dead(account: str, family: str) -> None:
    """Record that the account's refresh token was permanently rejected."""
    with _lock:
        _DEAD[_dead_key(account, family)] = time.time()
    logger.warning("OAuth refresh token for %s/%s rejected - auto-reauth queued", account, family)


def clear_token_dead(account: str, family: str) -> None:
    with _lock:
        _DEAD.pop(_dead_key(account, family), None)


def pending_flow(family: str = "graph") -> dict[str, Any] | None:
    """Return the pending auto-recovery device flow for family, if any."""
    with _lock:
        flow = _AUTO_FLOW
        if not flow or flow["family"] != family or flow["expires_at"] < time.time():
            return None
        return dict(flow)


def auto_flow() -> dict[str, Any] | None:
    """Public status of the pending auto-recovery flow (for REST/UI)."""
    flow = pending_flow()
    return flow or None


def ensure_auto_flow(family: str = "graph") -> dict[str, Any]:
    """Idempotent: return the pending flow for family, starting one if needed."""
    global _AUTO_FLOW
    with _lock:
        existing = pending_flow(family)
        if existing:
            return existing
        started = start_device_flow(scopes=family_scope(family))
        if not started.get("success"):
            logger.warning("auto-reauth: device flow could not start: %s", started.get("error"))
            return started
        _AUTO_FLOW = {
            "family": family,
            "device_code": started["device_code"],
            "user_code": started["user_code"],
            "verification_uri": started.get("verification_uri") or VERIFICATION_URI,
            "expires_at": time.time() + started.get("expires_in", 900),
            "interval": started.get("interval", 5),
            "message": started.get("message", ""),
        }
        logger.warning(
            "OAuth auto-reauth: enter code %s at %s (family=%s)",
            started["user_code"],
            _AUTO_FLOW["verification_uri"],
            family,
        )
        return dict(_AUTO_FLOW)


def _clear_flow() -> None:
    global _AUTO_FLOW
    _AUTO_FLOW = None


def guardian_tick() -> dict[str, Any]:
    """One pass of the OAuth guardian: poll pending flow, warm/repair tokens."""
    flow = pending_flow()
    if flow:
        result = poll_device_flow(flow["device_code"], scopes=family_scope(flow["family"]))
        status = result.get("status")
        if status == "authorized":
            logger.info("OAuth auto-reauth completed: %s", result.get("account"))
            _clear_flow()
            account = (result.get("account") or "").lower()
            with _lock:
                for key in list(_DEAD):
                    if not account or key[0] == account:
                        _DEAD.pop(key, None)
            # Fresh token is on disk (poll_device_flow saved it) - nothing to warm.
            return {"dead": len(_DEAD), "flow": False}
        elif status in ("declined", "expired", "error"):
            _clear_flow()  # restart with a fresh flow next tick

    store = _load_store()
    for key, raw in list(store.items()):
        if "|" not in key:
            continue
        account, family = key.rsplit("|", 1)
        if _dead_key(account, family) in _DEAD:
            continue
        try:
            token = OAuthToken(**raw)
        except TypeError:
            continue
        if time.time() < token.expires_at - _WARM_MARGIN:
            continue
        cid = client_id()
        if not cid:
            continue
        refreshed, err_code = refresh_access_token(cid, token.refresh_token, scopes=token.scope)
        if refreshed:
            refreshed.account = token.account
            save_token(refreshed)
        elif err_code in _PERMANENT_DEAD_CODES:
            mark_token_dead(account, family)

    with _lock:
        needs_flow = bool(_DEAD)
    if needs_flow:
        ensure_auto_flow()

    return {"dead": len(_DEAD), "flow": bool(pending_flow())}


def _guardian_loop() -> None:
    while True:
        try:
            guardian_tick()
        except Exception:
            logger.exception("OAuth guardian tick failed")
        time.sleep(_GUARDIAN_INTERVAL)


def start_guardian() -> None:
    """Start the background OAuth guardian thread (idempotent)."""
    global _GUARDIAN_THREAD
    with _lock:
        if _GUARDIAN_THREAD is not None and _GUARDIAN_THREAD.is_alive():
            return
        _GUARDIAN_THREAD = threading.Thread(target=_guardian_loop, name="oauth-guardian", daemon=True)
        _GUARDIAN_THREAD.start()
    logger.info("OAuth guardian started (interval=%ss)", _GUARDIAN_INTERVAL)
