"""Tests for the mail watcher auto-respond pipeline."""

from __future__ import annotations

import asyncio
import json

from email_mcp import watcher


class _Text:
    def __init__(self, text):
        self.text = text


class _Content:
    def __init__(self, text):
        self.content = [_Text(text)]


async def test_auto_respond_fresh_fetches_and_runs(monkeypatch, tmp_path):
    outcomes = []

    class FakeMCP:
        def __init__(self):
            self.calls = []

        async def call_tool(self, name, args):
            self.calls.append((name, args))
            if name == "fetch_email_detail":
                return _Content(json.dumps({"success": True, "text_body": "hello body"}))
            return {"success": True}

    async def fake_auto_respond(email, mcp_app=None, ai_router=None):
        outcomes.append(email)
        return {"matched": True, "rule": "test", "auto_sent": True}

    monkeypatch.setattr("email_mcp.autorespond.auto_respond", fake_auto_respond)

    mcp = FakeMCP()
    fresh = [{"id": "m1", "subject": "hello", "from": "a@x.com"}]
    results = await watcher._auto_respond_fresh(fresh, "default", "INBOX", mcp, None)

    assert len(results) == 1
    assert results[0]["matched"] is True
    # detail fetched with correct args
    assert mcp.calls[0][0] == "fetch_email_detail"
    assert mcp.calls[0][1]["email_id"] == "m1"
    # enriched email passed to engine with body + folder
    assert outcomes[0]["text_body"] == "hello body"
    assert outcomes[0]["folder"] == "INBOX"


async def test_auto_respond_fresh_bounded_to_10(monkeypatch):
    called = []

    class FakeMCP:
        async def call_tool(self, name, args):
            called.append(args)
            return _Content(json.dumps({"success": True, "text_body": "x"}))

    async def fake_auto_respond(email, mcp_app=None, ai_router=None):
        return {"matched": False, "message": "No rule matched"}

    monkeypatch.setattr("email_mcp.autorespond.auto_respond", fake_auto_respond)

    fresh = [{"id": f"m{i}", "subject": "s"} for i in range(15)]
    results = await watcher._auto_respond_fresh(fresh, "default", "INBOX", FakeMCP(), None)
    assert len(results) == 10  # bounded


async def test_start_watcher_auto_respond_param(monkeypatch):
    started = {}

    async def fake_loop(interval, webhook, services, mcp_app, auto_respond=False, ai_router=None, server_instance=None):
        started["auto_respond"] = auto_respond
        started["interval"] = interval
        while True:
            await asyncio.sleep(3600)

    monkeypatch.setattr(watcher, "_poll_loop", fake_loop)

    result = watcher.start_watcher(
        120, "", [{"name": "default", "folder": "INBOX"}], object(), auto_respond=True, persist=False
    )
    assert result["running"] is True
    await asyncio.sleep(0)  # let the task start
    assert started["auto_respond"] is True
    assert started["interval"] == 120
    watcher.stop_watcher(persist=False)


def _isolate_persist_file(monkeypatch, tmp_path):
    from pathlib import Path

    persist_file = Path(tmp_path / "watcher_config.json")
    monkeypatch.setattr(watcher, "_PERSIST_FILE", persist_file)
    return persist_file


async def test_start_watcher_persists_config(monkeypatch, tmp_path):
    persist_file = _isolate_persist_file(monkeypatch, tmp_path)

    async def fake_loop(*args, **kwargs):
        while True:
            await asyncio.sleep(3600)

    monkeypatch.setattr(watcher, "_poll_loop", fake_loop)

    watcher.start_watcher(90, "http://hook", None, object(), auto_respond=True)
    assert persist_file.is_file()
    cfg = json.loads(persist_file.read_text())
    assert cfg == {"enabled": True, "interval": 90, "webhook_url": "http://hook", "auto_respond": True}
    watcher.stop_watcher()
    assert json.loads(persist_file.read_text())["enabled"] is False


async def test_maybe_resume_watcher_noop_when_never_started(monkeypatch, tmp_path):
    _isolate_persist_file(monkeypatch, tmp_path)  # no file written -> nothing to resume
    result = await watcher.maybe_resume_watcher(object(), object())
    assert result == {"resumed": False}


async def test_maybe_resume_watcher_resumes_enabled_config(monkeypatch, tmp_path):
    persist_file = _isolate_persist_file(monkeypatch, tmp_path)
    persist_file.write_text(json.dumps({"enabled": True, "interval": 45, "webhook_url": "", "auto_respond": False}))

    captured = {}

    async def fake_loop(interval, webhook, services, mcp_app, auto_respond=False, ai_router=None, server_instance=None):
        captured["interval"] = interval
        captured["services"] = services
        captured["server_instance"] = server_instance
        while True:
            await asyncio.sleep(3600)

    monkeypatch.setattr(watcher, "_poll_loop", fake_loop)

    class FakeServer:
        services = {"default": object(), "graph": object()}

    server = FakeServer()
    result = await watcher.maybe_resume_watcher(object(), server)
    await asyncio.sleep(0)

    assert result["resumed"] is True
    assert captured["interval"] == 45
    assert captured["services"] is None  # auto mode -- re-derived from server_instance each cycle
    assert captured["server_instance"] is server
    watcher.stop_watcher(persist=False)


def test_all_configured_services_derives_from_server(monkeypatch):
    class FakeServer:
        services = {"default": object(), "graph": object()}

    result = watcher._all_configured_services(FakeServer())
    assert result == [{"name": "default", "folder": "INBOX"}, {"name": "graph", "folder": "INBOX"}]
    assert watcher._all_configured_services(None) == []
