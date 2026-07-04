"""Email templates -- save, manage, and use reusable email templates."""

from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any

_TEMPLATES: list[dict[str, Any]] = []
_FILE = Path(os.getenv("EMAIL_MCP_TEMPLATES_FILE", Path(__file__).resolve().parent.parent / "templates.json"))


def _load() -> None:
    global _TEMPLATES
    try:
        if _FILE.is_file():
            _TEMPLATES = json.loads(_FILE.read_text(encoding="utf-8"))
    except Exception:
        _TEMPLATES = []


def _save() -> None:
    try:
        _FILE.parent.mkdir(parents=True, exist_ok=True)
        _FILE.write_text(json.dumps(_TEMPLATES, indent=2, default=str), encoding="utf-8")
    except Exception:
        pass


def list_templates() -> list[dict[str, Any]]:
    _load()
    return _TEMPLATES


def add_template(name: str, subject: str = "", body: str = "", html: str = "", category: str = "") -> dict[str, Any]:
    _load()
    tmpl = {"id": str(uuid.uuid4())[:12], "name": name.strip(), "subject": subject.strip(), "body": body.strip(), "html": html.strip(), "category": category.strip(), "created_at": int(time.time())}
    _TEMPLATES.append(tmpl)
    _save()
    return {"success": True, "template": tmpl}


def delete_template(template_id: str) -> dict[str, Any]:
    _load()
    for i, t in enumerate(_TEMPLATES):
        if t["id"] == template_id:
            del _TEMPLATES[i]
            _save()
            return {"success": True, "message": f"Deleted template {t['name']!r}"}
    return {"success": False, "error": f"Template {template_id!r} not found"}


_load()
