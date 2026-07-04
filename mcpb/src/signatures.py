"""Per-account email signatures -- automatically appended to compose."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

_SIGNATURES: dict[str, str] = {}
_FILE = Path(os.getenv("EMAIL_MCP_SIGNATURES_FILE", Path(__file__).resolve().parent.parent / "signatures.json"))


def _load() -> None:
    global _SIGNATURES
    try:
        if _FILE.is_file():
            _SIGNATURES = json.loads(_FILE.read_text(encoding="utf-8"))
    except Exception:
        _SIGNATURES = {}


def _save() -> None:
    try:
        _FILE.parent.mkdir(parents=True, exist_ok=True)
        _FILE.write_text(json.dumps(_SIGNATURES, indent=2, default=str), encoding="utf-8")
    except Exception:
        pass


def get_signature(service: str = "default") -> dict[str, Any]:
    _load()
    return {"service": service, "signature": _SIGNATURES.get(service, "")}


def set_signature(service: str, signature: str) -> dict[str, Any]:
    _load()
    _SIGNATURES[service] = signature.strip()
    _save()
    return {"success": True, "service": service}


def delete_signature(service: str) -> dict[str, Any]:
    _load()
    _SIGNATURES.pop(service, None)
    _save()
    return {"success": True}


_load()
