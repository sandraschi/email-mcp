"""Tests for the Microsoft Graph email service (mocked HTTP)."""

from __future__ import annotations

import time

import httpx
import pytest

from email_mcp import oauth
from email_mcp.services.email_services import EmailServiceConfig
from email_mcp.services.graph_service import (
    GRAPH_BASE,
    GraphEmailService,
    _folder_id,
)


class FakeResponse:
    def __init__(self, status_code: int, json_data: dict):
        self.status_code = status_code
        self._json = json_data
        self.text = str(json_data)

    def json(self):
        return self._json


class FakeAsyncClient:
    """Stand-in for httpx.AsyncClient that records calls and returns canned data."""

    def __init__(self, responses: list[tuple[int, dict]]):
        self.responses = responses
        self.calls: list[tuple[str, str, dict, dict]] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def request(self, method, url, params=None, headers=None, json=None, timeout=None):
        self.calls.append((method, url, params or {}, headers or {}))
        status, data = self.responses.pop(0)
        return FakeResponse(status, data)


@pytest.fixture
def service(tmp_path, monkeypatch):
    monkeypatch.setenv("EMAIL_MCP_OAUTH_TOKEN_FILE", str(tmp_path / "tokens.json"))
    token = oauth.OAuthToken(
        account="sandra@hotmail.com",
        access_token="graph-tok",
        refresh_token="ref",
        scope=oauth.GRAPH_SCOPE,
        expires_at=time.time() + 3600,
    )
    oauth.save_token(token)
    cfg = EmailServiceConfig(name="graph", type="graph", config={"user": "sandra@hotmail.com"})
    return GraphEmailService(cfg)


def test_folder_id_mapping():
    assert _folder_id("INBOX") == "inbox"
    assert _folder_id("Sent") == "sentitems"
    assert _folder_id("Junk") == "junkemail"
    assert _folder_id("Trash") == "deleteditems"
    assert _folder_id("My Folder") == "My%20Folder"


def test_ready_requires_graph_token(service):
    assert service._ready() is True
    assert service.user == "sandra@hotmail.com"


async def test_check_inbox(service, monkeypatch):
    fake = FakeAsyncClient(
        [
            (
                200,
                {
                    "value": [
                        {
                            "id": "m1",
                            "subject": "Hello",
                            "from": {"emailAddress": {"name": "Ada", "address": "ada@x.com"}},
                            "receivedDateTime": "2026-07-31T10:00:00Z",
                            "isRead": False,
                        },
                        {
                            "id": "m2",
                            "subject": "Invoice",
                            "from": {"emailAddress": {"address": "billing@x.com"}},
                            "receivedDateTime": "2026-07-31T09:00:00Z",
                            "isRead": True,
                        },
                    ]
                },
            )
        ]
    )
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: fake)
    result = await service.check_inbox(unread_only=True, limit=10)
    assert result["success"] is True
    assert result["count"] == 2
    assert result["emails"][0]["id"] == "m1"
    assert "ada@x.com" in result["emails"][0]["from"]
    _, url, params, headers = fake.calls[0]
    assert url == f"{GRAPH_BASE}/me/mailFolders/inbox/messages"
    assert params["$filter"] == "isRead eq false"
    assert headers["Authorization"] == "Bearer graph-tok"


async def test_check_inbox_filters(service, monkeypatch):
    fake = FakeAsyncClient(
        [
            (
                200,
                {
                    "value": [
                        {
                            "id": "m1",
                            "subject": "Meeting notes",
                            "from": {"emailAddress": {"address": "boss@x.com"}},
                            "receivedDateTime": "2026-07-31T10:00:00Z",
                            "isRead": False,
                        },
                        {
                            "id": "m2",
                            "subject": "Invoice",
                            "from": {"emailAddress": {"address": "billing@x.com"}},
                            "receivedDateTime": "2026-07-31T09:00:00Z",
                            "isRead": True,
                        },
                    ]
                },
            )
        ]
    )
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: fake)
    result = await service.check_inbox(subject_contains="invoice")
    assert result["success"] is True
    assert result["count"] == 1
    assert result["emails"][0]["id"] == "m2"


async def test_send_email(service, monkeypatch):
    fake = FakeAsyncClient([(202, {})])
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: fake)
    result = await service.send_email(
        to="client@x.com",
        subject="Follow-up",
        body="Hello",
        cc=["cc@x.com"],
    )
    assert result["success"] is True
    _, url, _, headers = fake.calls[0]
    assert url == f"{GRAPH_BASE}/me/sendMail"
    assert headers["Content-Type"] == "application/json"
    assert headers["Authorization"] == "Bearer graph-tok"


async def test_send_email_payload(service, monkeypatch):
    captured = {}

    class CapturingClient(FakeAsyncClient):
        async def request(self, method, url, params=None, headers=None, json=None, timeout=None):
            captured["json"] = json
            return FakeResponse(202, {})

    monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: CapturingClient([]))
    result = await service.send_email(to="a@x.com", subject="Hi", body="B", html="<b>B</b>")
    assert result["success"] is True
    msg = captured["json"]["message"]
    assert msg["subject"] == "Hi"
    assert msg["body"]["contentType"] == "html"
    assert msg["body"]["content"] == "<b>B</b>"
    assert msg["toRecipients"] == [{"emailAddress": {"address": "a@x.com"}}]
    assert captured["json"]["saveToSentItems"] is True


async def test_fetch_message(service, monkeypatch):
    fake = FakeAsyncClient(
        [
            (
                200,
                {
                    "id": "m1",
                    "subject": "Hi",
                    "from": {"emailAddress": {"address": "a@x.com"}},
                    "toRecipients": [{"emailAddress": {"address": "me@x.com"}}],
                    "body": {"contentType": "text", "content": "hello world"},
                    "receivedDateTime": "2026-07-31T10:00:00Z",
                },
            )
        ]
    )
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: fake)
    result = await service.fetch_message("INBOX", "m1")
    assert result["success"] is True
    assert result["text_body"] == "hello world"
    assert result["html_body"] is None
    assert result["to"] == "me@x.com"


async def test_search(service, monkeypatch):
    fake = FakeAsyncClient(
        [
            (
                200,
                {
                    "value": [
                        {
                            "id": "m1",
                            "subject": "Invoice 42",
                            "from": {"emailAddress": {"address": "b@x.com"}},
                            "receivedDateTime": "2026-07-31T10:00:00Z",
                            "isRead": False,
                        }
                    ]
                },
            )
        ]
    )
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: fake)
    result = await service.search("invoice")
    assert result["success"] is True
    assert result["count"] == 1
    _, url, params, _ = fake.calls[0]
    assert url == f"{GRAPH_BASE}/me/messages"
    assert params["$search"] == '"invoice"'


async def test_no_token_reports_clear_error(monkeypatch, tmp_path):
    monkeypatch.setenv("EMAIL_MCP_OAUTH_TOKEN_FILE", str(tmp_path / "empty.json"))
    cfg = EmailServiceConfig(name="graph", type="graph", config={"user": "x@y.com"})
    svc = GraphEmailService(cfg)
    result = await svc.check_inbox()
    assert result["success"] is False
    assert "Graph" in result["error"]


async def test_oauth_401_raises_clear_error(service, monkeypatch):
    fake = FakeAsyncClient([(401, {"error": "invalid_token"})])
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: fake)
    result = await service.check_inbox()
    assert result["success"] is False
    assert "reconnect" in result["error"].lower()
