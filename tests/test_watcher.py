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

    async def fake_loop(interval, webhook, services, mcp_app, auto_respond=False, ai_router=None):
        started["auto_respond"] = auto_respond
        started["interval"] = interval
        while True:
            await asyncio.sleep(3600)

    monkeypatch.setattr(watcher, "_poll_loop", fake_loop)

    result = watcher.start_watcher(120, "", [{"name": "default", "folder": "INBOX"}], object(), auto_respond=True)
    assert result["running"] is True
    await asyncio.sleep(0)  # let the task start
    assert started["auto_respond"] is True
    assert started["interval"] == 120
    watcher.stop_watcher()
