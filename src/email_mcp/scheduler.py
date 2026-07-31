"""Scheduled send -- queue emails to be sent at a specific time."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from pathlib import Path
from typing import Any

_SCHEDULED: list[dict[str, Any]] = []
_FILE = Path(os.getenv("EMAIL_MCP_SCHEDULED_FILE", Path(__file__).resolve().parent.parent / "scheduled.json"))
_task: asyncio.Task | None = None

logger = logging.getLogger(__name__)


def _load() -> None:
    global _SCHEDULED
    try:
        if _FILE.is_file():
            _SCHEDULED = json.loads(_FILE.read_text(encoding="utf-8"))
    except Exception:
        _SCHEDULED = []


def _save() -> None:
    try:
        _FILE.parent.mkdir(parents=True, exist_ok=True)
        _FILE.write_text(json.dumps(_SCHEDULED, indent=2, default=str) + "\n", encoding="utf-8")
    except Exception:
        pass


def schedule_send(to: str, subject: str, body: str, send_at: float, service: str = "default") -> dict[str, Any]:
    _load()
    entry = {
        "id": str(__import__("uuid").uuid4())[:12],
        "to": to,
        "subject": subject,
        "body": body,
        "service": service,
        "send_at": send_at,
        "status": "scheduled",
        "created_at": time.time(),
    }
    _SCHEDULED.append(entry)
    _save()
    return {"success": True, "scheduled": entry}


def list_scheduled() -> list[dict[str, Any]]:
    _load()
    return sorted(_SCHEDULED, key=lambda e: e.get("send_at", 0))


def cancel_scheduled(scheduled_id: str) -> dict[str, Any]:
    _load()
    for i, e in enumerate(_SCHEDULED):
        if e["id"] == scheduled_id:
            del _SCHEDULED[i]
            _save()
            return {"success": True, "message": "Cancelled"}
    return {"success": False, "error": f"Scheduled send {scheduled_id!r} not found"}


async def _process_queue(mcp_app) -> None:
    """Background loop: send due emails every 15 seconds."""
    while True:
        try:
            _load()
            now = time.time()
            due = [e for e in _SCHEDULED if e["status"] == "scheduled" and e["send_at"] <= now]
            for entry in due:
                try:
                    await mcp_app.call_tool(
                        "send_email",
                        {
                            "to": entry["to"],
                            "subject": entry["subject"],
                            "body": entry["body"],
                            "service": entry["service"],
                        },
                    )
                    entry["status"] = "sent"
                    entry["sent_at"] = time.time()
                    logger.info("Scheduled send delivered: %s", entry["subject"])
                except Exception as e:
                    entry["status"] = "failed"
                    entry["error"] = str(e)
                    logger.warning("Scheduled send failed: %s", e)
            if due:
                _save()
        except Exception as e:
            logger.warning("Scheduler cycle error: %s", e)
        await asyncio.sleep(15)


def start_scheduler(mcp_app) -> dict[str, Any]:
    global _task
    if _task is not None and not _task.done():
        return {"running": True, "message": "Already running"}
    loop = asyncio.get_event_loop()
    _task = loop.create_task(_process_queue(mcp_app))
    return {"running": True, "message": "Scheduler started"}


_load()
