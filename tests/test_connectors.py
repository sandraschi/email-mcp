"""Tests for the fleet connectors (aiwatcher / robofang), mocked HTTP."""

from __future__ import annotations

import httpx
import pytest

from email_mcp import connectors


class FakeResponse:
    def __init__(self, status_code: int, json_data: dict | None = None):
        self.status_code = status_code
        self._json = json_data or {}
        self.text = str(json_data or {})

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("boom", request=None, response=self)

    def json(self):
        return self._json


class FakeAsyncClient:
    def __init__(self, response: FakeResponse):
        self.response = response
        self.calls: list[tuple[str, str, dict | None]] = []
        self.last_headers: dict | None = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def post(self, url, json=None, headers=None):
        self.calls.append(("POST", url, json))
        self.last_headers = headers
        return self.response

    async def get(self, url):
        self.calls.append(("GET", url, None))
        return self.response


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("EMAIL_MCP_AIWATCHER_URL", "http://127.0.0.1:10946")
    monkeypatch.setenv("EMAIL_MCP_ROBOFANG_URL", "http://127.0.0.1:10871")
    monkeypatch.delenv("EMAIL_MCP_AIWATCHER_KEY", raising=False)


async def test_push_aiwatcher(monkeypatch):
    fake = FakeAsyncClient(FakeResponse(200))
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: fake)
    result = await connectors.push_aiwatcher("Urgent email", "Invoice overdue", url="https://x", urgency_hint=8.0)
    assert result["success"] is True
    method, url, payload = fake.calls[0]
    assert method == "POST"
    assert url == "http://127.0.0.1:10946/api/fleet/ingest"
    assert payload["title"] == "Urgent email"
    assert payload["source"] == "email-mcp"
    assert payload["urgency_hint"] == 8.0
    assert payload["url"] == "https://x"


async def test_push_aiwatcher_sends_key_when_set(monkeypatch):
    monkeypatch.setenv("EMAIL_MCP_AIWATCHER_KEY", "sekret")
    fake = FakeAsyncClient(FakeResponse(200))
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: fake)
    result = await connectors.push_aiwatcher("t")
    assert result["success"] is True
    assert fake.last_headers["X-AIWatcher-Key"] == "sekret"


async def test_push_aiwatcher_requires_title(monkeypatch):
    result = await connectors.push_aiwatcher("")
    assert result["success"] is False
    assert "title" in result["error"]


async def test_push_aiwatcher_fails_soft(monkeypatch):
    fake = FakeAsyncClient(FakeResponse(500))
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: fake)
    result = await connectors.push_aiwatcher("t")
    assert result["success"] is False
    assert "error" in result


async def test_push_robofang(monkeypatch):
    fake = FakeAsyncClient(FakeResponse(200))
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: fake)
    result = await connectors.push_robofang("sandra@hotmail.com", "Backup failed", subject="Alert")
    assert result["success"] is True
    _method, url, payload = fake.calls[0]
    assert url == "http://127.0.0.1:10871/api/hooks/email"
    assert payload["from_addr"] == "sandra@hotmail.com"
    assert payload["subject"] == "Alert"
    assert payload["body"] == "Backup failed"


async def test_push_robofang_requires_from(monkeypatch):
    result = await connectors.push_robofang("", "x")
    assert result["success"] is False
    assert "from_addr" in result["error"]


async def test_connector_health_all_online(monkeypatch):
    fake = FakeAsyncClient(FakeResponse(200))
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: fake)
    result = await connectors.connector_health()
    assert result["success"] is True
    assert result["connectors"]["aiwatcher"]["online"] is True
    assert result["connectors"]["robofang"]["online"] is True


async def test_connector_health_offline(monkeypatch):
    class FailingClient(FakeAsyncClient):
        async def get(self, url):
            raise ConnectionError("refused")

    monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: FailingClient(FakeResponse(200)))
    result = await connectors.connector_health()
    assert result["connectors"]["aiwatcher"]["online"] is False
    assert "refused" in result["connectors"]["aiwatcher"]["error"]


async def test_connector_disabled_when_unset(monkeypatch):
    monkeypatch.delenv("EMAIL_MCP_AIWATCHER_URL", raising=False)
    monkeypatch.delenv("EMAIL_MCP_ROBOFANG_URL", raising=False)
    result = await connectors.connector_health()
    assert result["connectors"]["aiwatcher"]["enabled"] is False
    assert result["connectors"]["robofang"]["enabled"] is False
