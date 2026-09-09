"""Mail Watcher -- background IMAP polling with webhook notifications.

Polls configured email services at intervals and fires webhook POSTs
when new unread emails arrive. Designed to integrate with robofang,
fleet-agent, or any webhook listener.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# ── Watcher state ──────────────────────────────────────────────────────────

_watcher_task: asyncio.Task | None = None
_watcher_config: dict[str, Any] = {}


def _make_service_key(service: str, folder: str) -> str:
    return f"{service}:{folder}"


# ── Persisted config (survives process restarts) ────────────────────────────
# Same runtime-dir convention as autorespond.py's rules file: LOCALAPPDATA in
# the Tauri wrapper, repo src/ otherwise.


def _runtime_dir() -> Path | None:
    base = os.getenv("LOCALAPPDATA", "")
    if base and os.getenv("EMAIL_MCP_TAURI", "").lower() in ("1", "true", "yes"):
        return Path(base) / "ai.fleet.email-mcp"
    return None


_default_data_dir = _runtime_dir() or Path(__file__).resolve().parent.parent
_PERSIST_FILE = Path(os.getenv("EMAIL_MCP_WATCHER_CONFIG", str(_default_data_dir / "watcher_config.json")))


def _load_persisted_config() -> dict[str, Any] | None:
    try:
        if _PERSIST_FILE.is_file():
            return json.loads(_PERSIST_FILE.read_text(encoding="utf-8"))
    except Exception:
        logger.warning("Failed to read watcher config", exc_info=True)
    return None


def _save_persisted_config(cfg: dict[str, Any]) -> None:
    """Atomic write (temp file + replace) so a crash mid-write can't corrupt the config."""
    try:
        _PERSIST_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = _PERSIST_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
        tmp.replace(_PERSIST_FILE)
    except Exception:
        logger.warning("Failed to persist watcher config", exc_info=True)


def _all_configured_services(server_instance: Any) -> list[dict]:
    """Every currently-configured account, INBOX folder. Re-derived fresh so
    an account added after the watcher started is picked up on the next poll."""
    if server_instance is None:
        return []
    try:
        return [{"name": name, "folder": "INBOX"} for name in server_instance.services]
    except Exception:
        return []


async def _poll_loop(
    interval_s: int,
    webhook_url: str,
    services: list[dict] | None,
    mcp_app,
    auto_respond: bool = False,
    ai_router=None,
    server_instance: Any = None,
) -> None:
    """Background loop: poll services, POST new email IDs to webhook, auto-respond.

    services=None means "auto": the active service list is re-derived from
    server_instance.services at the top of every cycle, so accounts added
    later are watched without restarting the watcher. A pinned services list
    is used verbatim (advanced/manual use).
    """
    known_ids: dict[str, set[str]] = {}
    logger.info(
        "Mail watcher started (interval=%ss, webhook=%s, auto_respond=%s, mode=%s)",
        interval_s,
        webhook_url,
        auto_respond,
        "auto (all configured services)" if not services else "pinned",
    )

    while True:
        try:
            active_services = services or _all_configured_services(server_instance)
            for svc in active_services:
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
    services: list[dict] | None,
    mcp_app,
    auto_respond: bool = False,
    ai_router=None,
    server_instance: Any = None,
    persist: bool = True,
) -> dict[str, Any]:
    """Start the background mail watcher.

    services=None (the default from the webapp) watches every currently
    configured account's INBOX and keeps re-deriving that list each poll, so
    accounts added later are covered automatically. Pass an explicit list to
    pin the watcher to specific service/folder pairs instead.

    auto_respond=True runs the auto-respond rule engine on fresh mail
    (replies, filter actions, notifications) in addition to webhooks.

    persist=True (default) saves this config to disk so the watcher resumes
    automatically the next time the server starts (see maybe_resume_watcher).
    """
    global _watcher_task, _watcher_config

    if _watcher_task is not None and not _watcher_task.done():
        return {
            "running": True,
            "message": "Watcher already running",
            "services": [s["name"] for s in _watcher_config.get("services") or []] or "auto",
        }

    _watcher_config = {
        "interval": interval_s,
        "webhook_url": webhook_url,
        "services": services,
        "auto_respond": auto_respond,
    }
    if persist:
        _save_persisted_config(
            {"enabled": True, "interval": interval_s, "webhook_url": webhook_url, "auto_respond": auto_respond}
        )
    loop = asyncio.get_event_loop()
    _watcher_task = loop.create_task(
        _poll_loop(
            interval_s,
            webhook_url,
            services,
            mcp_app,
            auto_respond=auto_respond,
            ai_router=ai_router,
            server_instance=server_instance,
        )
    )
    return {
        "running": True,
        "message": f"Watcher started (interval={interval_s}s, auto_respond={auto_respond})",
        "services": [s["name"] for s in services] if services else "auto (all configured services)",
    }


def stop_watcher(persist: bool = True) -> dict[str, Any]:
    """Stop the background mail watcher."""
    global _watcher_task
    if _watcher_task is None or _watcher_task.done():
        return {"running": False, "message": "No watcher running"}
    _watcher_task.cancel()
    _watcher_task = None
    if persist:
        cfg = _load_persisted_config() or {}
        cfg["enabled"] = False
        _save_persisted_config(cfg)
    return {"running": False, "message": "Watcher stopped"}


def watcher_status() -> dict[str, Any]:
    """Get watcher status."""
    running = _watcher_task is not None and not _watcher_task.done()
    persisted = _load_persisted_config() or {}
    return {
        "running": running,
        "config": _watcher_config if running else None,
        "persisted_enabled": bool(persisted.get("enabled")),
    }


async def maybe_resume_watcher(mcp_app, server_instance: Any) -> dict[str, Any]:
    """Called once at server startup: resume the watcher if it was running
    (enabled) when the process last stopped. No-op if never started or last
    stopped explicitly. Always auto-watches every currently configured
    service (services=None) since a persisted pinned list would go stale.
    """
    cfg = _load_persisted_config()
    if not cfg or not cfg.get("enabled"):
        return {"resumed": False}

    ai_router = None
    if cfg.get("auto_respond"):
        try:
            from email_mcp.ai import AIRouter

            ai_router = AIRouter(mcp_app)
        except Exception:
            logger.warning("ai_router unavailable for watcher resume", exc_info=True)

    result = start_watcher(
        interval_s=cfg.get("interval", 60),
        webhook_url=cfg.get("webhook_url", ""),
        services=None,
        mcp_app=mcp_app,
        auto_respond=bool(cfg.get("auto_respond")),
        ai_router=ai_router,
        server_instance=server_instance,
        persist=False,
    )
    logger.info("Mail watcher auto-resumed from persisted config: %s", result.get("message"))
    return {"resumed": True, **result}
