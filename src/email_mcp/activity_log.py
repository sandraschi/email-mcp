from __future__ import annotations

import csv
import io
import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from .auth import authenticate

# Severity order for minimum-level filtering (WEBAPP_LOGS_PAGE.md §2.1:
# `level` is a *minimum*, not an exact match).
_LEVEL_ORDER = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40, "CRITICAL": 50}


class ActivityLog:
    def __init__(self, max_entries: int = 5000):
        self._entries: list[dict[str, Any]] = []
        self._max = max_entries
        self.dropped = 0  # entries evicted by rotation (surfaced in /api/logs/stats)

    def add(self, level: str, detail: str, kind: str = "", meta: dict | None = None) -> str:
        entry_id = uuid.uuid4().hex[:12]
        self._entries.append(
            {
                "id": entry_id,
                "timestamp": datetime.now(UTC).isoformat(),
                "level": level,
                "kind": kind,
                "detail": detail,
                "meta": meta or {},
            }
        )
        if len(self._entries) > self._max:
            self._entries.pop(0)
            self.dropped += 1
        return entry_id

    def query(
        self,
        limit: int = 50,
        offset: int = 0,
        level: str = "",
        kind: str = "",
        search: str = "",
        sort: str = "desc",
        after_id: str = "",
    ) -> dict[str, Any]:
        items = self._entries
        if level:
            # Minimum-level semantics per WEBAPP_LOGS_PAGE.md §2.1.
            threshold = _LEVEL_ORDER.get(level.upper(), 0)
            items = [e for e in items if _LEVEL_ORDER.get(e["level"], 0) >= threshold]
        if kind:
            items = [e for e in items if e["kind"] == kind]
        if search:
            q = search.lower()
            items = [e for e in items if q in e["detail"].lower()]
        if after_id:
            try:
                idx = next(i for i, e in enumerate(items) if e["id"] == after_id)
                items = items[idx + 1 :]
            except StopIteration:
                pass
        if sort == "desc":
            items = list(reversed(items))
        total = len(items)
        return {
            "entries": items[offset : offset + limit],
            "total": total,
            "limit": limit,
            "offset": offset,
            "max_entries": self._max,
            "sort": sort,
        }

    def clear(self) -> None:
        self._entries.clear()

    def _level_ok(self, entry_level: str, level: str) -> bool:
        if not level:
            return True
        return _LEVEL_ORDER.get(entry_level, 0) >= _LEVEL_ORDER.get(level.upper(), 0)

    def export_csv(self, level: str = "", kind: str = "", search: str = "") -> str:
        items = self._entries
        if level:
            items = [e for e in items if self._level_ok(e["level"], level)]
        if kind:
            items = [e for e in items if e["kind"] == kind]
        if search:
            q = search.lower()
            items = [e for e in items if q in e["detail"].lower()]
        out = io.StringIO()
        w = csv.writer(out)
        w.writerow(["id", "timestamp", "level", "kind", "detail"])
        for e in items:
            w.writerow([e["id"], e["timestamp"], e["level"], e["kind"], e["detail"]])
        return out.getvalue()

    def export_json(self, level: str = "", kind: str = "", search: str = "") -> str:
        import json

        items = self._entries
        if level:
            items = [e for e in items if self._level_ok(e["level"], level)]
        if kind:
            items = [e for e in items if e["kind"] == kind]
        if search:
            q = search.lower()
            items = [e for e in items if q in e["detail"].lower()]
        return json.dumps(items, indent=2)


class ActivityLogHandler(logging.Handler):
    """logging.Handler bridge into the ring buffer (WEBAPP_LOGS_PAGE.md §4).

    Attach to the root logger on startup so uvicorn/app INFO+ lines appear
    with kind=server; tool calls carry kind=tool_call via log-record `extra`.
    """

    def __init__(self, log: ActivityLog):
        super().__init__()
        self.log = log

    @staticmethod
    def _kind_for(record: logging.LogRecord) -> str:
        explicit = getattr(record, "kind", "")
        if explicit:
            return str(explicit)
        name = record.name or ""
        if name.startswith(("email_mcp.tools", "email_mcp.timeout_middleware")):
            return "tool_call"
        return "server"

    def emit(self, record: logging.LogRecord) -> None:
        try:
            detail = record.getMessage()
            if record.exc_info and not record.exc_text:
                try:
                    detail += "\n" + self.formatException(record.exc_info)
                except Exception:
                    pass
            meta: dict[str, Any] = {"logger": record.name}
            tool = getattr(record, "tool", "")
            if tool:
                meta["tool"] = tool
            self.log.add(record.levelname, detail, self._kind_for(record), meta)
        except Exception:
            self.handleError(record)


def attach_activity_handler(log: ActivityLog) -> ActivityLogHandler:
    """Attach the bridge to the root logger once; returns the handler."""
    root = logging.getLogger()
    for existing in root.handlers:
        if isinstance(existing, ActivityLogHandler) and existing.log is log:
            return existing
    handler = ActivityLogHandler(log)
    root.addHandler(handler)
    return handler


def create_log_router(log: ActivityLog) -> APIRouter:
    # Whole router is auth-gated: DELETE must be (WEBAPP_LOGS_PAGE.md §2),
    # and the dashboard always sends credentials anyway.
    router = APIRouter(dependencies=[Depends(authenticate)])

    @router.get("/logs/stats")
    async def get_log_stats():
        return {
            "storage": "memory",
            "max_entries": log._max,
            "count": len(log._entries),
            "dropped": log.dropped,
        }

    @router.get("/logs")
    async def get_logs(
        limit: int = Query(50, ge=1, le=500),
        offset: int = Query(0, ge=0),
        level: str = Query(""),
        kind: str = Query(""),
        search: str = Query(""),
        sort: str = Query("desc"),
        after_id: str = Query(""),
    ):
        return log.query(
            limit=limit, offset=offset, level=level, kind=kind, search=search, sort=sort, after_id=after_id
        )

    @router.delete("/logs")
    async def clear_logs():
        log.clear()
        return {"success": True}

    @router.get("/logs/export")
    async def export_logs(
        format: str = Query("json"), level: str = Query(""), kind: str = Query(""), search: str = Query("")
    ):
        if format == "csv":
            return StreamingResponse(
                io.StringIO(log.export_csv(level=level, kind=kind, search=search)),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=logs.csv"},
            )
        return StreamingResponse(
            io.StringIO(log.export_json(level=level, kind=kind, search=search)),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=logs.json"},
        )

    return router
