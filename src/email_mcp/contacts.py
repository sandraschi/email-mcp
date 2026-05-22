"""Contact store — import, manage, and search contacts for email composition.

Stores contacts in a JSON file. Supports CSV, vCard (.vcf), and manual entry.
"""

from __future__ import annotations

import csv
import io
import json
import os
import re
import time
import uuid
from pathlib import Path
from typing import Any

_CONTACTS: list[dict[str, Any]] = []
_CONTACTS_FILE = Path(os.getenv("EMAIL_MCP_CONTACTS_FILE", Path(__file__).resolve().parent.parent / "contacts.json"))


def _load() -> None:
    global _CONTACTS
    try:
        if _CONTACTS_FILE.is_file():
            _CONTACTS = json.loads(_CONTACTS_FILE.read_text(encoding="utf-8"))
    except Exception:
        _CONTACTS = []


def _save() -> None:
    try:
        _CONTACTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        _CONTACTS_FILE.write_text(json.dumps(_CONTACTS, indent=2, default=str), encoding="utf-8")
    except Exception:
        pass


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def list_contacts() -> list[dict[str, Any]]:
    _load()
    return sorted(_CONTACTS, key=lambda c: (c.get("name", "") or "").lower())


def search_contacts(query: str) -> list[dict[str, Any]]:
    _load()
    q = query.lower()
    return [c for c in _CONTACTS if q in (c.get("name", "") or "").lower() or q in (c.get("email", "") or "").lower()]


def add_contact(name: str, email: str, phone: str = "", notes: str = "", group: str = "") -> dict[str, Any]:
    _load()
    email_n = _normalize_email(email)
    if any(_normalize_email(c.get("email", "")) == email_n for c in _CONTACTS):
        return {"success": False, "error": f"Contact with email '{email}' already exists"}
    contact = {
        "id": str(uuid.uuid4())[:12],
        "name": name.strip(),
        "email": email_n,
        "phone": phone.strip(),
        "notes": notes.strip(),
        "group": group.strip(),
        "created_at": int(time.time()),
    }
    _CONTACTS.append(contact)
    _save()
    return {"success": True, "contact": contact}


def update_contact(contact_id: str, updates: dict[str, Any]) -> dict[str, Any]:
    _load()
    for c in _CONTACTS:
        if c["id"] == contact_id:
            for key in ("name", "email", "phone", "notes", "group"):
                if key in updates:
                    c[key] = updates[key].strip() if isinstance(updates[key], str) else updates[key]
            _save()
            return {"success": True, "contact": c}
    return {"success": False, "error": f"Contact {contact_id!r} not found"}


def delete_contact(contact_id: str) -> dict[str, Any]:
    _load()
    for i, c in enumerate(_CONTACTS):
        if c["id"] == contact_id:
            del _CONTACTS[i]
            _save()
            return {"success": True, "message": f"Deleted {c.get('name', contact_id)}"}
    return {"success": False, "error": f"Contact {contact_id!r} not found"}


def import_csv(text: str) -> dict[str, Any]:
    """Import contacts from CSV. Expected columns: name, email (required), phone, notes, group."""
    reader = csv.DictReader(io.StringIO(text))
    imported = 0
    errors: list[str] = []
    for i, row in enumerate(reader):
        name = (row.get("name") or "").strip()
        email = _normalize_email(row.get("email") or "")
        if not email:
            errors.append(f"Row {i + 1}: no email")
            continue
        result = add_contact(name, email, row.get("phone", ""), row.get("notes", ""), row.get("group", ""))
        if result.get("success"):
            imported += 1
        else:
            errors.append(f"Row {i + 1}: {result.get('error')}")
    return {"success": True, "imported": imported, "errors": errors}


def import_vcard(text: str) -> dict[str, Any]:
    """Import contacts from vCard (.vcf) format."""
    imported = 0
    errors: list[str] = []
    entries = re.split(r"^BEGIN:VCARD\s*$", text, flags=re.MULTILINE)
    for entry in entries:
        if "END:VCARD" not in entry:
            continue
        name = ""
        email = ""
        phone = ""
        for line in entry.splitlines():
            if line.upper().startswith("FN:"):
                name = line.split(":", 1)[1].strip() if ":" in line else ""
            elif line.upper().startswith("EMAIL"):
                email = line.split(":", 1)[1].strip() if ":" in line else ""
            elif line.upper().startswith("TEL"):
                phone = line.split(":", 1)[1].strip() if ":" in line else ""
        if email:
            result = add_contact(name, email, phone)
            if result.get("success"):
                imported += 1
            else:
                errors.append(f"{email}: {result.get('error')}")
    return {"success": True, "imported": imported, "errors": errors}


def get_groups() -> list[str]:
    _load()
    groups: set[str] = set()
    for c in _CONTACTS:
        if c.get("group"):
            groups.add(c["group"])
    return sorted(groups)


# Load at module init
_load()
