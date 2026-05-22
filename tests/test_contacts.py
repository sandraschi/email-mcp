"""Tests for the contacts module (CSV, vCard, Google, Microsoft import)."""

from __future__ import annotations

from pathlib import Path

import pytest

from email_mcp.contacts import (
    add_contact,
    delete_contact,
    get_groups,
    import_csv,
    import_vcard,
    list_contacts,
    search_contacts,
    update_contact,
)


# Use a temp file for contacts so tests don't clobber real data
@pytest.fixture(autouse=True)
def _isolate_contacts_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Redirect contacts to a temp file for each test."""
    monkeypatch.setenv("EMAIL_MCP_CONTACTS_FILE", str(tmp_path / "contacts.json"))
    # Reimport to trigger _load with the new path
    import importlib

    import email_mcp.contacts as c

    importlib.reload(c)


class TestContactCRUD:
    def test_add_contact(self) -> None:
        result = add_contact("Alice", "alice@test.com", "555-0100", "Friend", "Friends")
        assert result["success"] is True
        assert result["contact"]["name"] == "Alice"
        assert result["contact"]["email"] == "alice@test.com"
        assert result["contact"]["group"] == "Friends"

    def test_add_duplicate_email(self) -> None:
        add_contact("Alice", "alice@test.com")
        result = add_contact("Alice2", "alice@test.com")
        assert result["success"] is False
        assert "already exists" in result["error"]

    def test_add_normalizes_email(self) -> None:
        add_contact("Alice", "ALICE@TEST.COM")
        contacts = list_contacts()
        assert contacts[0]["email"] == "alice@test.com"

    def test_list_contacts(self) -> None:
        add_contact("Alice", "alice@test.com")
        add_contact("Bob", "bob@test.com")
        contacts = list_contacts()
        assert len(contacts) == 2

    def test_search_by_name(self) -> None:
        add_contact("Alice Johnson", "alice@test.com")
        add_contact("Bob Smith", "bob@test.com")
        results = search_contacts("alice")
        assert len(results) == 1
        assert results[0]["name"] == "Alice Johnson"

    def test_search_by_email(self) -> None:
        add_contact("Alice", "alice@test.com")
        results = search_contacts("alice@test")
        assert len(results) == 1

    def test_search_no_results(self) -> None:
        results = search_contacts("nonexistent")
        assert results == []

    def test_update_contact(self) -> None:
        result = add_contact("Alice", "alice@test.com")
        cid = result["contact"]["id"]
        update_contact(cid, {"name": "Alice Updated", "phone": "555-9999"})
        contacts = list_contacts()
        assert contacts[0]["name"] == "Alice Updated"
        assert contacts[0]["phone"] == "555-9999"

    def test_delete_contact(self) -> None:
        result = add_contact("Alice", "alice@test.com")
        cid = result["contact"]["id"]
        delete_contact(cid)
        assert len(list_contacts()) == 0

    def test_delete_nonexistent(self) -> None:
        result = delete_contact("nonexistent")
        assert result["success"] is False

    def test_get_groups(self) -> None:
        add_contact("Alice", "a@t.com", group="Friends")
        add_contact("Bob", "b@t.com", group="Work")
        add_contact("Charlie", "c@t.com", group="Friends")
        groups = get_groups()
        assert "Friends" in groups
        assert "Work" in groups
        assert len(groups) == 2


class TestContactImport:
    def test_import_csv(self) -> None:
        csv_data = "name,email,phone,notes,group\nAlice,alice@t.com,555-0100,Friend,Friends\nBob,bob@t.com,555-0200,Colleague,Work"
        result = import_csv(csv_data)
        assert result["success"] is True
        assert result["imported"] == 2
        assert len(result["errors"]) == 0
        assert len(list_contacts()) == 2

    def test_import_csv_no_email_skipped(self) -> None:
        csv_data = "name,email\nAlice,\nBob,bob@t.com"
        result = import_csv(csv_data)
        assert result["imported"] == 1
        assert len(result["errors"]) == 1

    def test_import_csv_duplicate(self) -> None:
        add_contact("Alice", "alice@t.com")
        csv_data = "name,email\nAlice,alice@t.com\nBob,bob@t.com"
        result = import_csv(csv_data)
        assert result["imported"] == 1  # Only Bob
        assert len(result["errors"]) == 1  # Alice duplicate

    def test_import_vcard(self) -> None:
        vcard = """BEGIN:VCARD
FN:Alice Johnson
EMAIL:alice@test.com
TEL:555-0100
END:VCARD
BEGIN:VCARD
FN:Bob Smith
EMAIL:bob@test.com
TEL:555-0200
END:VCARD"""
        result = import_vcard(vcard)
        assert result["success"] is True
        assert result["imported"] == 2
        contacts = list_contacts()
        assert contacts[0]["name"] == "Alice Johnson"
        assert contacts[1]["phone"] == "555-0200"

    def test_import_vcard_no_email(self) -> None:
        vcard = "BEGIN:VCARD\nFN:No Email\nEND:VCARD"
        result = import_vcard(vcard)
        assert result["imported"] == 0

    def test_import_vcard_mixed(self) -> None:
        vcard = "BEGIN:VCARD\nFN:Alice\nEMAIL:a@t.com\nEND:VCARD\nBEGIN:VCARD\nFN:No Email\nEND:VCARD"
        result = import_vcard(vcard)
        assert result["imported"] == 1
