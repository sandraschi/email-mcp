"""Persistent service credentials (Settings-saved services survive restarts).

RATIONALE: services configured at runtime (Settings UI, quick-setup, MCP
configure_service via REST) lived only in memory - a backend restart wiped
them and the user had to re-enter passwords. That is not "save". This module
stores them in src/service_credentials.json (gitignored, same pattern as
drafts.json) and reloads them at startup. Explicit environment config
(.env / EMAIL_SERVICES) always wins over this file (setdefault semantics).

Format: {"services": {"<name>": {"type": str, "enabled": bool, "config": {...}}}}
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def credentials_file() -> Path:
    """Path of the persisted credentials file (overridable for tests)."""
    override = os.getenv("EMAIL_MCP_CREDENTIALS_FILE", "").strip()
    if override:
        return Path(override)
    return Path(__file__).resolve().parent.parent / "service_credentials.json"


def load_persisted_services() -> dict[str, dict[str, Any]]:
    """Return {name: {type, enabled, config}} from disk, {} when absent/broken."""
    path = credentials_file()
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        logger.warning("Ignoring unreadable service credentials file %s: %s", path, exc)
        return {}
    services = data.get("services") if isinstance(data, dict) else None
    if not isinstance(services, dict):
        logger.warning("Ignoring malformed service credentials file %s (no 'services' dict)", path)
        return {}
    valid: dict[str, dict[str, Any]] = {}
    for name, entry in services.items():
        if isinstance(entry, dict) and isinstance(entry.get("config"), dict):
            valid[str(name)] = {
                "type": str(entry.get("type", "smtp")),
                "enabled": bool(entry.get("enabled", True)),
                "config": dict(entry["config"]),
            }
    return valid


def save_persisted_service(name: str, type: str, config: dict[str, Any], enabled: bool = True) -> bool:
    """Persist one service (atomic write). Returns True on success."""
    path = credentials_file()
    try:
        existing = load_persisted_services()
    except Exception:  # pragma: no cover - load never raises, belt and braces
        existing = {}
    existing[name] = {"type": type, "enabled": enabled, "config": dict(config)}
    payload = {"services": existing}
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, indent=2)
            os.replace(tmp, path)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
        return True
    except OSError as exc:
        logger.error("Could not persist service %r to %s: %s", name, path, exc)
        return False


def remove_persisted_service(name: str) -> bool:
    """Drop one service from the persisted file. True when the file was updated."""
    path = credentials_file()
    existing = load_persisted_services()
    if name not in existing:
        return False
    del existing[name]
    try:
        fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump({"services": existing}, fh, indent=2)
            os.replace(tmp, path)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
        return True
    except OSError as exc:
        logger.error("Could not remove persisted service %r from %s: %s", name, path, exc)
        return False
