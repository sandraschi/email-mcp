"""Tests for mailing list preset loading."""

import json
from pathlib import Path

import pytest

from email_mcp.mailing_lists import MailingListEntry, load_mailing_list_entries


def test_mailing_list_entry_defaults() -> None:
    e = MailingListEntry(id="x", service="default", folder="INBOX")
    assert e.limit == 5
    assert e.unread_only is True


def test_load_from_env_json(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("EMAIL_MCP_MAILING_LISTS_FILE", raising=False)
    raw = json.dumps(
        [
            {
                "id": "alphasignal",
                "service": "default",
                "folder": "INBOX.Lists.AlphaSignal",
                "limit": 3,
                "unread_only": True,
            }
        ]
    )
    monkeypatch.setenv("EMAIL_MCP_MAILING_LISTS", raw)
    entries, err = load_mailing_list_entries()
    assert err is None
    assert len(entries) == 1
    assert entries[0].id == "alphasignal"
    assert entries[0].folder == "INBOX.Lists.AlphaSignal"


def test_load_invalid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("EMAIL_MCP_MAILING_LISTS_FILE", raising=False)
    monkeypatch.setenv("EMAIL_MCP_MAILING_LISTS", "[not json")
    entries, err = load_mailing_list_entries()
    assert entries == []
    assert err is not None


def test_load_from_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("EMAIL_MCP_MAILING_LISTS", raising=False)
    p = tmp_path / "lists.json"
    p.write_text(
        json.dumps([{"id": "a", "folder": "INBOX.A", "from_contains": "news@"}]),
        encoding="utf-8",
    )
    monkeypatch.setenv("EMAIL_MCP_MAILING_LISTS_FILE", str(p))
    entries, err = load_mailing_list_entries()
    assert err is None
    assert entries[0].from_contains == "news@"


def test_duplicate_id_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("EMAIL_MCP_MAILING_LISTS_FILE", raising=False)
    monkeypatch.setenv(
        "EMAIL_MCP_MAILING_LISTS",
        json.dumps(
            [
                {"id": "dup", "folder": "INBOX.A"},
                {"id": "dup", "folder": "INBOX.B"},
            ]
        ),
    )
    entries, err = load_mailing_list_entries()
    assert entries == []
    assert err is not None and "Duplicate" in err
