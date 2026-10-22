"""Service credential persistence tests (no network).

Settings-saved services must survive backend restarts via the credentials file.
"""

import json

from email_mcp import persistence


def _isolate(monkeypatch, tmp_path):
    monkeypatch.setenv("EMAIL_MCP_CREDENTIALS_FILE", str(tmp_path / "creds.json"))


def test_save_and_load_roundtrip(monkeypatch, tmp_path):
    _isolate(monkeypatch, tmp_path)
    assert (
        persistence.save_persisted_service(
            "gmail", "smtp", {"imap_server": "imap.gmail.com", "imap_password": "x"}, enabled=True
        )
        is True
    )
    loaded = persistence.load_persisted_services()
    assert loaded["gmail"]["type"] == "smtp"
    assert loaded["gmail"]["enabled"] is True
    assert loaded["gmail"]["config"]["imap_server"] == "imap.gmail.com"


def test_missing_file_loads_empty(monkeypatch, tmp_path):
    _isolate(monkeypatch, tmp_path)
    assert persistence.load_persisted_services() == {}


def test_corrupt_file_loads_empty(monkeypatch, tmp_path):
    _isolate(monkeypatch, tmp_path)
    path = persistence.credentials_file()
    path.write_text("{not json", encoding="utf-8")
    assert persistence.load_persisted_services() == {}


def test_remove_service(monkeypatch, tmp_path):
    _isolate(monkeypatch, tmp_path)
    persistence.save_persisted_service("gmail", "smtp", {"a": 1})
    assert persistence.remove_persisted_service("gmail") is True
    assert persistence.load_persisted_services() == {}
    assert persistence.remove_persisted_service("gmail") is False


def test_file_is_valid_json_with_services_key(monkeypatch, tmp_path):
    _isolate(monkeypatch, tmp_path)
    persistence.save_persisted_service("yahoo", "smtp", {"x": 1})
    raw = json.loads(persistence.credentials_file().read_text(encoding="utf-8"))
    assert set(raw.keys()) == {"services"}
    assert raw["services"]["yahoo"]["type"] == "smtp"
