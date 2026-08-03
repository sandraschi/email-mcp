"""Mail Watcher -- background IMAP polling with webhook notifications.

Polls configured email services at intervals and fires webhook POSTs
when new unread emails arrive. Designed to integrate with robofang,
fleet-agent, or any webhook listener.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# ── Watcher state ──────────────────────────────────────────────────────────

_watcher_task: asyncio.Task | None = None
_watcher_config: dict[str, Any] = {}


def _make_service_key(service: str, folder: str) -> str:
    return f"{service}:{folder}"


async def _poll_loop(
    interval_s: int,
    webhook_url: str,
    services: list[dict],
    mcp_app,
    auto_respond: bool = False,
    ai_router=None,
) -> None:
    """Background loop: poll services, POST new email IDs to webhook, auto-respond."""
    known_ids: dict[str, set[str]] = {}
    logger.info(
        "Mail watcher started (interval=%ss, webhook=%s, auto_respond=%s, services=%s)",
        interval_s,
        webhook_url,
        auto_respond,
        [s["name"] for s in services],
    )

    while True:
        try:
            for svc in services:
                svc_name = svc["name"]
                folder = svc.get("folder", "INBOX")
                key = _make_service_key(svc_name, folder)
                try:
                    result = await mcp_app.call_tool(
                        "check_inbox",
                        {"service": svc_name, "folder": folder, "unread_only": True, "limit": 50},
                    )
                    # Extract emails from CallToolResult
                    emails = []
                    if hasattr(result, "content"):
                        for c in result.content:
                            if hasattr(c, "text"):
                                try:
                                    data = json.loads(c.text)
                                    if isinstance(data, dict):
                                        emails = data.get("emails", [])
                                except Exception:
                                    pass
                    elif isinstance(result, dict):
                        emails = result.get("emails", [])

                    new_ids = {e["id"] for e in emails if e.get("id")}
                    if key not in known_ids:
                        known_ids[key] = new_ids
                        continue

                    fresh = new_ids - known_ids[key]
                    if fresh:
                        fresh_emails = [e for e in emails if e["id"] in fresh]
                        logger.info("New emails on %s: %d", key, len(fresh_emails))
                        await _fire_webhook(webhook_url, svc_name, folder, fresh_emails)
                        if auto_respond:
                            await _auto_respond_fresh(fresh_emails, svc_name, folder, mcp_app, ai_router)
                    known_ids[key] = new_ids

                except Exception as exc:
                    logger.warning("Poll failed for %s: %s", key, exc)

        except Exception as exc:
            logger.warning("Poll cycle error: %s", exc)

        await asyncio.sleep(interval_s)


async def _auto_respond_fresh(
    fresh_emails: list[dict], service: str, folder: str, mcp_app, ai_router
) -> list[dict[str, Any]]:
    """Fetch full bodies for fresh emails and run the auto-respond engine.

    Bounded to 10 emails per poll cycle to keep latency predictable.
    Returns per-email outcomes.
    """
    from email_mcp.autorespond import auto_respond

    outcomes: list[dict[str, Any]] = []
    for email in fresh_emails[:10]:
        try:
            detail = await mcp_app.call_tool(
                "fetch_email_detail",
                {"email_id": email["id"], "service": service, "folder": folder},
            )
            body = ""
            if hasattr(detail, "content"):
                for c in detail.content:
                    if hasattr(c, "text"):
                        try:
                            data = json.loads(c.text)
                            if isinstance(data, dict):
                                body = data.get("text_body") or data.get("html_body") or ""
                        except Exception:
                            pass
            elif isinstance(detail, dict) and detail.get("success"):
                body = detail.get("text_body") or detail.get("html_body") or ""

            enriched = {
                "id": email["id"],
                "subject": email.get("subject", ""),
                "from": email.get("from", ""),
                "text_body": body,
                "folder": folder,
            }
            outcome = await auto_respond(enriched, mcp_app=mcp_app, ai_router=ai_router)
            if outcome.get("matched"):
                logger.info(
                    "Auto-respond fired for %s (rule=%s): %s",
                    enriched["subject"],
                    outcome.get("rule"),
                    outcome,
                )
            outcomes.append(outcome)
        except Exception as exc:
            logger.warning("Auto-respond failed for %s: %s", email.get("id"), exc)
    return outcomes


async def _fire_webhook(webhook_url: str, service: str, folder: str, emails: list[dict]) -> None:
    """POST new emails to the configured webhook URL."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                webhook_url,
                json={
                    "event": "new_email",
                    "service": service,
                    "folder": folder,
                    "count": len(emails),
                    "emails": [
                        {"id": e["id"], "subject": e.get("subject", ""), "from": e.get("from", "")} for e in emails
                    ],
                    "timestamp": time.time(),
                },
            )
    except Exception as exc:
        logger.warning("Webhook POST failed to %s: %s", webhook_url, exc)


def start_watcher(
    interval_s: int,
    webhook_url: str,
    services: list[dict],
    mcp_app,
    auto_respond: bool = False,
    ai_router=None,
) -> dict[str, Any]:
    """Start the background mail watcher.

    auto_respond=True runs the auto-respond rule engine on fresh mail
    (replies, filter actions, notifications) in addition to webhooks.
    """
    global _watcher_task, _watcher_config

    if _watcher_task is not None and not _watcher_task.done():
        return {
            "running": True,
            "message": "Watcher already running",
            "services": [s["name"] for s in _watcher_config.get("services", [])],
        }

    _watcher_config = {
        "interval": interval_s,
        "webhook_url": webhook_url,
        "services": services,
        "auto_respond": auto_respond,
    }
    loop = asyncio.get_event_loop()
    _watcher_task = loop.create_task(
        _poll_loop(interval_s, webhook_url, services, mcp_app, auto_respond=auto_respond, ai_router=ai_router)
    )
    return {
        "running": True,
        "message": f"Watcher started (interval={interval_s}s, auto_respond={auto_respond})",
        "services": [s["name"] for s in services],
    }


def stop_watcher() -> dict[str, Any]:
    """Stop the background mail watcher."""
    global _watcher_task
    if _watcher_task is None or _watcher_task.done():
        return {"running": False, "message": "No watcher running"}
    _watcher_task.cancel()
    _watcher_task = None
    return {"running": False, "message": "Watcher stopped"}


def watcher_status() -> dict[str, Any]:
    """Get watcher status."""
    running = _watcher_task is not None and not _watcher_task.done()
    return {
        "running": running,
        "config": _watcher_config if running else None,
    }
