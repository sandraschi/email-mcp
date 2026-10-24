"""User-managed mailing-list presets (webapp-editable) merged over env presets.

RATIONALE: mailing_lists.py loads EMAIL_MCP_MAILING_LISTS / FILE (env-only,
read-only from the webapp). The Mailing Lists page needs CRUD without
restarting the service. This module stores user presets in
src/mailing_lists_user.json (gitignored, same pattern as
service_credentials.json / drafts.json) and merges them over env entries
(env wins on id collision, setdefault semantics).

Schema (same as MailingListEntry): {id, service, folder, limit, unread_only,
from_contains?, subject_contains?} plus optional description.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def user_file() -> Path:
    override = os.getenv("EMAIL_MCP_MAILING_LISTS_USER_FILE", "").strip()
    if override:
        return Path(override)
    return Path(__file__).resolve().parent.parent / "mailing_lists_user.json"


def load_user_presets() -> dict[str, dict[str, Any]]:
    path = user_file()
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        logger.warning("Ignoring unreadable mailing-lists user file %s: %s", path, exc)
        return {}
    items = data.get("lists") if isinstance(data, dict) else None
    if not isinstance(items, dict):
        return {}
    return {str(k): dict(v) for k, v in items.items() if isinstance(v, dict)}


def _save_all(items: dict[str, dict[str, Any]]) -> bool:
    path = user_file()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = Path(tempfile.mkstemp(dir=str(path.parent), prefix=".mailing-")[1])
        tmp.write_text(json.dumps({"lists": items}, indent=2), encoding="utf-8")
        tmp.replace(path)
        return True
    except OSError as exc:
        logger.warning("Cannot save mailing-lists user file %s: %s", path, exc)
        return False


def list_merged() -> tuple[list[dict[str, Any]], list[str]]:
    """Return (merged presets, readonly_ids from env). Env wins on collision."""
    from .mailing_lists import load_mailing_list_entries

    env_entries, _err = load_mailing_list_entries()
    merged: dict[str, dict[str, Any]] = {}
    for e in env_entries:
        merged[e.id] = {
            "id": e.id,
            "service": e.service,
            "folder": e.folder,
            "limit": e.limit,
            "unread_only": e.unread_only,
            "from_contains": e.from_contains,
            "subject_contains": e.subject_contains,
            "readonly": True,
            "source": "env",
        }
    readonly_ids = list(merged.keys())
    for lid, row in load_user_presets().items():
        if lid in merged:
            continue
        merged[lid] = {
            "id": lid,
            "service": str(row.get("service", "default")),
            "folder": str(row.get("folder", "INBOX")),
            "limit": int(row.get("limit", 5) or 5),
            "unread_only": bool(row.get("unread_only", False)),
            "from_contains": row.get("from_contains"),
            "subject_contains": row.get("subject_contains"),
            "description": str(row.get("description", "")),
            "readonly": False,
            "source": "user",
        }
    return list(merged.values()), readonly_ids


def upsert_user_preset(entry: dict[str, Any]) -> tuple[bool, str | None]:
    lid = str(entry.get("id", "")).strip()
    if not lid:
        return False, "id is required"
    if not lid.replace("-", "").replace("_", "").isalnum():
        return False, "id must be alphanumeric with -/_"
    items = load_user_presets()
    # Refuse to shadow an env preset id.
    from .mailing_lists import load_mailing_list_entries

    env_entries, _ = load_mailing_list_entries()
    if any(e.id == lid for e in env_entries):
        return False, f"id {lid!r} is defined in env presets (readonly)"
    items[lid] = {
        "service": str(entry.get("service", "default") or "default"),
        "folder": str(entry.get("folder", "INBOX") or "INBOX"),
        "limit": max(1, min(50, int(entry.get("limit", 5) or 5))),
        "unread_only": bool(entry.get("unread_only", False)),
        "from_contains": entry.get("from_contains") or None,
        "subject_contains": entry.get("subject_contains") or None,
        "description": str(entry.get("description", "") or ""),
    }
    if not _save_all(items):
        return False, "cannot write user presets file"
    return True, None


def delete_user_preset(list_id: str) -> tuple[bool, str | None]:
    items = load_user_presets()
    if list_id not in items:
        return False, f"user preset {list_id!r} not found (env presets are readonly)"
    del items[list_id]
    if not _save_all(items):
        return False, "cannot write user presets file"
    return True, None


def get_merged(list_id: str) -> dict[str, Any] | None:
    presets, _ = list_merged()
    for p in presets:
        if p["id"] == list_id:
            return p
    return None


def strip_html_to_text(html: str, limit: int = 6000) -> str:
    """Minimal HTML -> text for digest building (no bs4 dependency)."""
    import html as _html
    import re as _re

    if not html:
        return ""
    text = _re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html)
    text = _re.sub(r"(?is)<br\s*/?>", "\n", text)
    text = _re.sub(r"(?is)</(p|div|h[1-6]|li|tr|table)>", "\n", text)
    text = _re.sub(r"(?is)<[^>]+>", " ", text)
    text = _html.unescape(text)
    text = _re.sub(r"[ \t\xa0]+", " ", text)
    text = _re.sub(r"\n{3,}", "\n\n", text)
    text = _re.sub(r"(?i)https?://[^\s\"'<>]+", lambda m: "\n" + m.group(0), text)
    return text.strip()[:limit]
