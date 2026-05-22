"""Auto-respond engine — rule-based matching + AI drafting + pending queue."""

from __future__ import annotations

import json
import os
import re
import time
import uuid
from pathlib import Path
from typing import Any

_RULES: list[dict[str, Any]] = []
_RULES_FILE = Path(os.getenv("EMAIL_MCP_AUTORESPOND_RULES", Path(__file__).resolve().parent.parent / "autorespond_rules.json"))

_PENDING: list[dict[str, Any]] = []
_PENDING_FILE = Path(os.getenv("EMAIL_MCP_AUTORESPOND_PENDING", Path(__file__).resolve().parent.parent / "autorespond_pending.json"))


def _load_rules() -> None:
    global _RULES
    try:
        if _RULES_FILE.is_file():
            _RULES = json.loads(_RULES_FILE.read_text(encoding="utf-8"))
    except Exception:
        _RULES = []


def _save_rules() -> None:
    try:
        _RULES_FILE.parent.mkdir(parents=True, exist_ok=True)
        _RULES_FILE.write_text(json.dumps(_RULES, indent=2, default=str), encoding="utf-8")
    except Exception:
        pass


def _load_pending() -> None:
    global _PENDING
    try:
        if _PENDING_FILE.is_file():
            _PENDING = json.loads(_PENDING_FILE.read_text(encoding="utf-8"))
    except Exception:
        _PENDING = []


def _save_pending() -> None:
    try:
        _PENDING_FILE.parent.mkdir(parents=True, exist_ok=True)
        _PENDING_FILE.write_text(json.dumps(_PENDING, indent=2, default=str), encoding="utf-8")
    except Exception:
        pass


# ── Rule CRUD ──────────────────────────────────────────────────────────────


def list_rules() -> list[dict[str, Any]]:
    _load_rules()
    return _RULES


def add_rule(
    name: str,
    match_field: str = "subject",
    match_pattern: str = "",
    reply_body: str = "",
    reply_subject: str = "",
    use_ai: bool = False,
    auto_send: bool = False,
    ai_prompt: str = "",
    service: str = "default",
) -> dict[str, Any]:
    _load_rules()
    rule = {
        "id": str(uuid.uuid4())[:12],
        "name": name.strip(),
        "match_field": match_field,
        "match_pattern": match_pattern.strip(),
        "reply_body": reply_body.strip(),
        "reply_subject": reply_subject.strip(),
        "use_ai": use_ai,
        "auto_send": auto_send,
        "ai_prompt": ai_prompt.strip(),
        "service": service,
        "enabled": True,
        "created_at": int(time.time()),
    }
    _RULES.append(rule)
    _save_rules()
    return {"success": True, "rule": rule}


def update_rule(rule_id: str, updates: dict[str, Any]) -> dict[str, Any]:
    _load_rules()
    for r in _RULES:
        if r["id"] == rule_id:
            for key in ("name", "match_field", "match_pattern", "reply_body", "reply_subject", "use_ai", "auto_send", "ai_prompt", "service", "enabled"):
                if key in updates:
                    r[key] = updates[key]
            _save_rules()
            return {"success": True, "rule": r}
    return {"success": False, "error": f"Rule {rule_id!r} not found"}


def delete_rule(rule_id: str) -> dict[str, Any]:
    _load_rules()
    for i, r in enumerate(_RULES):
        if r["id"] == rule_id:
            del _RULES[i]
            _save_rules()
            return {"success": True, "message": f"Deleted rule {r['name']!r}"}
    return {"success": False, "error": f"Rule {rule_id!r} not found"}


# ── Rule matching ──────────────────────────────────────────────────────────


def match_rule(email: dict[str, Any]) -> dict[str, Any] | None:
    """Find the first enabled rule matching this email."""
    _load_rules()
    for rule in _RULES:
        if not rule.get("enabled", True):
            continue
        field = email.get(rule.get("match_field", "subject"), "")
        pattern = rule.get("match_pattern", "")
        if not pattern:
            continue
        try:
            if re.search(pattern, str(field), re.IGNORECASE):
                return rule
        except re.error:
            continue
    return None


# ── Pending queue (for human approval) ─────────────────────────────────────


def list_pending() -> list[dict[str, Any]]:
    _load_pending()
    return sorted(_PENDING, key=lambda p: p.get("created_at", 0), reverse=True)


def add_pending(email: dict[str, Any], reply_body: str, reply_subject: str, rule_id: str, service: str = "default") -> dict[str, Any]:
    _load_pending()
    entry = {
        "id": str(uuid.uuid4())[:12],
        "email_id": email.get("id", ""),
        "email_subject": email.get("subject", ""),
        "email_from": email.get("from", ""),
        "email_body": email.get("text_body", email.get("body", "")),
        "reply_body": reply_body,
        "reply_subject": reply_subject,
        "rule_id": rule_id,
        "service": service,
        "status": "pending",
        "created_at": int(time.time()),
    }
    _PENDING.append(entry)
    _save_pending()
    return entry


def approve_pending(pending_id: str, mcp_app=None) -> dict[str, Any]:
    _load_pending()
    for p in _PENDING:
        if p["id"] == pending_id:
            p["status"] = "approved"
            _save_pending()
            return {"success": True, "pending": p, "message": f"Approved reply to {p['email_subject']!r}"}
    return {"success": False, "error": f"Pending entry {pending_id!r} not found"}


def reject_pending(pending_id: str) -> dict[str, Any]:
    _load_pending()
    for p in _PENDING:
        if p["id"] == pending_id:
            p["status"] = "rejected"
            _save_pending()
            return {"success": True, "message": "Rejected"}
    return {"success": False, "error": f"Pending entry {pending_id!r} not found"}


def delete_pending(pending_id: str) -> dict[str, Any]:
    _load_pending()
    for i, p in enumerate(_PENDING):
        if p["id"] == pending_id:
            del _PENDING[i]
            _save_pending()
            return {"success": True, "message": "Deleted"}
    return {"success": False, "error": f"Pending entry {pending_id!r} not found"}


# ── Auto-respond on new email (called by watcher) ──────────────────────────


async def auto_respond(email: dict[str, Any], mcp_app=None, ai_router=None) -> dict[str, Any]:
    """Auto-respond to a new email. Called by the watcher when mail arrives."""
    import logging

    logger = logging.getLogger(__name__)

    rule = match_rule(email)
    if not rule:
        return {"matched": False, "message": "No rule matched"}

    reply_subject = rule.get("reply_subject", "") or f"Re: {email.get('subject', '')}"
    reply_body = rule.get("reply_body", "")

    if rule.get("use_ai") and ai_router:
        body_text = (email.get("text_body") or email.get("body", ""))[:2000]
        prompt = rule.get("ai_prompt", "") or (f"Write a friendly reply. Be concise.\nFrom: {email.get('from', '')}\nSubject: {email.get('subject', '')}\nBody: {body_text}")
        reply_body = await ai_router.route_query(prompt)

    if rule.get("auto_send") and mcp_app and reply_body:
        try:
            result = await mcp_app.call_tool(
                "send_email",
                {
                    "to": email.get("from", ""),
                    "subject": reply_subject,
                    "body": reply_body,
                    "service": rule.get("service", "default"),
                },
            )
            logger.info("Auto-sent reply to %s: %s", email.get("from", ""), result)
            return {"matched": True, "auto_sent": True, "rule": rule["name"], "reply_subject": reply_subject}
        except Exception as e:
            logger.warning("Auto-send failed: %s", e)
            return {"matched": True, "auto_sent": False, "error": str(e), "rule": rule["name"]}

    if reply_body:
        add_pending(email, reply_body, reply_subject, rule["id"], rule.get("service", "default"))
        logger.info("Added pending reply for %s: %s", email.get("from", ""), reply_subject)
        return {"matched": True, "queued": True, "rule": rule["name"], "reply_subject": reply_subject}

    return {"matched": True, "action": "none", "rule": rule["name"]}


# Initialize
_load_rules()
_load_pending()
