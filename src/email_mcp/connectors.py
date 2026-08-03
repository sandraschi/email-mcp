"""Outbound fleet connectors: aiwatcher (fleet ingest) and robofang (email hook).

email-mcp pushes events into the fleet pipeline the same way arxiv-mcp and
vla-mcp do:

- aiwatcher:  POST {EMAIL_MCP_AIWATCHER_URL}/api/fleet/ingest
              {title, summary, source, url, urgency_hint}
              (header X-AIWatcher-Key when EMAIL_MCP_AIWATCHER_KEY is set)
- robofang:   POST {EMAIL_MCP_ROBOFANG_URL}/api/hooks/email
              {from_addr, subject, body}  -> robofang inbox processing

Both connectors are opt-in (empty URL = disabled) and fail soft: a connector
error is logged and returned in the result dict, never raised to the caller.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

AIWATCHER_DEFAULT = "http://127.0.0.1:10946"
ROBOFANG_DEFAULT = "http://127.0.0.1:10871"

TIMEOUT = 8.0


def _aiwatcher_url() -> str:
    return os.getenv("EMAIL_MCP_AIWATCHER_URL", "").strip() or AIWATCHER_DEFAULT


def _aiwatcher_key() -> str:
    return os.getenv("EMAIL_MCP_AIWATCHER_KEY", "").strip()


def _robofang_url() -> str:
    return os.getenv("EMAIL_MCP_ROBOFANG_URL", "").strip() or ROBOFANG_DEFAULT


def aiwatcher_enabled() -> bool:
    return bool(os.getenv("EMAIL_MCP_AIWATCHER_URL", "").strip())


def robofang_enabled() -> bool:
    return bool(os.getenv("EMAIL_MCP_ROBOFANG_URL", "").strip())


async def push_aiwatcher(
    title: str,
    summary: str = "",
    *,
    source: str = "email-mcp",
    url: str = "",
    urgency_hint: float | None = None,
) -> dict[str, Any]:
    """Push an event into aiwatcher's fleet ingest (news/alert pipeline)."""
    if not title or not title.strip():
        return {"success": False, "connector": "aiwatcher", "error": "title is required"}
    payload: dict[str, Any] = {"title": title.strip()[:300], "summary": (summary or "")[:2000], "source": source}
    if url:
        payload["url"] = url
    if urgency_hint is not None:
        payload["urgency_hint"] = max(0.0, min(10.0, float(urgency_hint)))
    headers = {"Content-Type": "application/json"}
    key = _aiwatcher_key()
    if key:
        headers["X-AIWatcher-Key"] = key
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.post(f"{_aiwatcher_url()}/api/fleet/ingest", json=payload, headers=headers)
            resp.raise_for_status()
        logger.info("aiwatcher ingest ok: %s", title[:60])
        return {"success": True, "connector": "aiwatcher", "title": title.strip()[:300]}
    except Exception as exc:
        logger.warning("aiwatcher ingest failed: %s", exc)
        return {"success": False, "connector": "aiwatcher", "error": str(exc)}


async def push_robofang(
    from_addr: str,
    body: str,
    subject: str = "",
) -> dict[str, Any]:
    """Send an email into robofang's inbox hook for processing/reply."""
    if not from_addr or not from_addr.strip():
        return {"success": False, "connector": "robofang", "error": "from_addr is required"}
    payload = {"from_addr": from_addr.strip(), "subject": (subject or "")[:300], "body": (body or "")[:20000]}
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.post(f"{_robofang_url()}/api/hooks/email", json=payload)
            resp.raise_for_status()
        logger.info("robofang email hook ok: %s", from_addr)
        return {"success": True, "connector": "robofang", "from_addr": from_addr.strip()}
    except Exception as exc:
        logger.warning("robofang email hook failed: %s", exc)
        return {"success": False, "connector": "robofang", "error": str(exc)}


async def connector_health() -> dict[str, Any]:
    """Probe both connectors and report reachability + enabled state."""
    result: dict[str, Any] = {"success": True, "connectors": {}}

    aw_enabled = aiwatcher_enabled()
    if aw_enabled:
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                resp = await client.get(f"{_aiwatcher_url()}/health")
            ok = resp.status_code == 200
            result["connectors"]["aiwatcher"] = {
                "enabled": True,
                "url": _aiwatcher_url(),
                "online": ok,
                "error": None if ok else f"HTTP {resp.status_code}",
            }
        except Exception as exc:
            result["connectors"]["aiwatcher"] = {
                "enabled": True,
                "url": _aiwatcher_url(),
                "online": False,
                "error": str(exc),
            }
    else:
        result["connectors"]["aiwatcher"] = {
            "enabled": False,
            "url": "",
            "online": False,
            "error": "not configured (set EMAIL_MCP_AIWATCHER_URL)",
        }

    rf_enabled = robofang_enabled()
    if rf_enabled:
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                resp = await client.get(f"{_robofang_url()}/")
            ok = resp.status_code == 200
            result["connectors"]["robofang"] = {
                "enabled": True,
                "url": _robofang_url(),
                "online": ok,
                "error": None if ok else f"HTTP {resp.status_code}",
            }
        except Exception as exc:
            result["connectors"]["robofang"] = {
                "enabled": True,
                "url": _robofang_url(),
                "online": False,
                "error": str(exc),
            }
    else:
        result["connectors"]["robofang"] = {
            "enabled": False,
            "url": "",
            "online": False,
            "error": "not configured (set EMAIL_MCP_ROBOFANG_URL)",
        }

    return result
