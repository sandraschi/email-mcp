"""Named mailing-list presets (JSON) for mailing_list_latest / mailing_lists_catalog."""

from __future__ import annotations

import json
import os
from pathlib import Path

from pydantic import BaseModel, Field, field_validator


class MailingListEntry(BaseModel):
    """One subscription the user configured (e.g. Alpha Signal → label folder)."""

    id: str = Field(..., min_length=1, description="Stable id for tools, e.g. alphasignal")
    service: str = Field(default="default", description="Email service name from list_services")
    folder: str = Field(default="INBOX", description="IMAP folder (e.g. Gmail label path)")
    limit: int = Field(default=5, ge=1, le=50, description="Max messages to return")
    unread_only: bool = Field(
        default=True,
        description="If True, only UNSEEN (typical for newest drop)",
    )
    from_contains: str | None = Field(
        default=None,
        description="Optional case-insensitive substring match on From (after fetch)",
    )
    subject_contains: str | None = Field(
        default=None,
        description="Optional case-insensitive substring match on Subject",
    )

    @field_validator("id")
    @classmethod
    def strip_id(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("id cannot be empty")
        return s


def load_mailing_list_entries() -> tuple[list[MailingListEntry], str | None]:
    """Load mailing list presets from ``EMAIL_MCP_MAILING_LISTS`` or ``EMAIL_MCP_MAILING_LISTS_FILE``.

    Returns:
        (entries, error_message). On success error_message is None.
    """
    raw_path = os.getenv("EMAIL_MCP_MAILING_LISTS_FILE", "").strip()
    if raw_path:
        p = Path(raw_path)
        if not p.is_file():
            return [], f"EMAIL_MCP_MAILING_LISTS_FILE not found: {p}"
        try:
            raw = p.read_text(encoding="utf-8")
        except OSError as e:
            return [], f"Cannot read EMAIL_MCP_MAILING_LISTS_FILE: {e}"
    else:
        raw = os.getenv("EMAIL_MCP_MAILING_LISTS", "").strip()
        if not raw:
            return [], ("No mailing lists configured. Set EMAIL_MCP_MAILING_LISTS (JSON array) or EMAIL_MCP_MAILING_LISTS_FILE (path to JSON). See README.")

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        return [], f"Invalid JSON in mailing-list config: {e}"

    if not isinstance(data, list):
        return [], "Mailing list config must be a JSON array of objects"

    out: list[MailingListEntry] = []
    seen: set[str] = set()
    for i, row in enumerate(data):
        if not isinstance(row, dict):
            return [], f"Entry {i} must be an object"
        try:
            entry = MailingListEntry.model_validate(row)
        except Exception as e:
            return [], f"Entry {i} ({row}): {e}"
        if entry.id in seen:
            return [], f"Duplicate mailing list id: {entry.id!r}"
        seen.add(entry.id)
        out.append(entry)

    return out, None
