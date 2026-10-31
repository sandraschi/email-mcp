"""Tests for the disposable (throwaway) email service (mocked HTTP, no network)."""

from __future__ import annotations

import httpx
import pytest

from email_mcp.services import disposable_service
from email_mcp.services.disposable_service import DisposableEmailService
from email_mcp.services.email_services import EmailServiceConfig, EmailServiceFactory


class FakeResponse:
    def __init__(self, status_code: int, json_data: dict):
        self.status_code = status_code
        self._json = json_data

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(f"HTTP {self.status_code}", request=None, response=None)  # type: ignore[arg-type]


class FakeAsyncClient:
    """Canned mail.tm API: each request pops the next (status, json) pair."""

    def __init__(self, responses: list[tuple[int, dict]]):
        self._responses = list(responses)
        self.calls: list[tuple[str, str, dict | None]] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    def _next(self, method: str, url: str, json: dict | None):
        self.calls.append((method, url, json))
        status, data = self._responses.pop(0)
        return FakeResponse(status, data)

    async def get(self, url: str, **kwargs):
        return self._next("GET", url, None)

    async def post(self, url: str, **kwargs):
        return self._next("POST", url, kwargs.get("json"))

    async def request(self, method: str, url: str, **kwargs):
        return self._next(method, url, kwargs.get("json"))


def _patch(responses: list[tuple[int, dict]], monkeypatch: pytest.MonkeyPatch) -> FakeAsyncClient:
    fake = FakeAsyncClient(responses)
    monkeypatch.setattr(disposable_service.httpx, "AsyncClient", lambda **kwargs: fake)
    return fake


def _cfg(**overrides) -> EmailServiceConfig:
    base = {"address": "x@mail.tm", "password": "pw", "token": "tok"}
    base.update(overrides)
    return EmailServiceConfig(name="throwaway", type="disposable", config=base)


async def test_mint_creates_account_and_token(monkeypatch):
    fake = _patch(
        [
            # mail.tm returns a bare JSON array for /domains (Hydra dict for /messages)
            (200, [{"domain": "mail.tm"}]),
            (201, {"id": "a1", "address": "emailmcp-x@mail.tm"}),
            (200, {"token": "jwt-1", "id": "a1"}),
        ],
        monkeypatch,
    )
    cfg = await DisposableEmailService.mint()
    assert cfg["address"].endswith("@mail.tm")
    assert cfg["token"] == "jwt-1"  # noqa: S105 (test fixture, not a secret)
    assert len(cfg["password"]) >= 20
    assert [c[0] for c in fake.calls] == ["GET", "POST", "POST"]


async def test_mint_no_domains_raises(monkeypatch):
    _patch([(200, {"hydra:member": [], "hydra:totalItems": 0})], monkeypatch)
    with pytest.raises(RuntimeError, match="no usable domains"):
        await DisposableEmailService.mint()


async def test_check_inbox_maps_and_filters(monkeypatch):
    msgs = {
        "hydra:member": [
            {
                "id": "m1",
                "subject": "Welcome aboard",
                "from": {"address": "news@example.com", "name": "News"},
                "intro": "hi",
                "seen": False,
                "createdAt": "2026-10-30T10:00:00Z",
            },
            {
                "id": "m2",
                "subject": "Read already",
                "from": {"address": "old@example.com", "name": ""},
                "intro": "old",
                "seen": True,
                "createdAt": "2026-10-30T09:00:00Z",
            },
        ],
        "hydra:totalItems": 2,
    }
    _patch([(200, msgs)], monkeypatch)
    svc = DisposableEmailService(_cfg())
    res = await svc.check_inbox(limit=10)
    assert res["success"] and res["count"] == 2
    assert res["emails"][0]["from"] == "News <news@example.com>"
    assert res["emails"][1]["from"] == "old@example.com"

    _patch([(200, msgs)], monkeypatch)
    unread = await svc.check_inbox(unread_only=True)
    assert unread["count"] == 1 and unread["emails"][0]["id"] == "m1"

    _patch([(200, msgs)], monkeypatch)
    filtered = await svc.check_inbox(subject_contains="welcome")
    assert filtered["count"] == 1


async def test_send_is_honestly_refused(monkeypatch):
    svc = DisposableEmailService(_cfg())
    res = await svc.send_email("a@b.com", "s", "b")
    assert res["success"] is False and "receive-only" in res["error"]


async def test_token_refresh_on_401(monkeypatch):
    msgs = {"hydra:member": [], "hydra:totalItems": 0}
    fake = _patch(
        [
            (401, {"message": "expired"}),
            (200, {"token": "jwt-2", "id": "a1"}),
            (200, msgs),
        ],
        monkeypatch,
    )
    svc = DisposableEmailService(_cfg(token="stale"))
    res = await svc.check_inbox()
    assert res["success"] is True
    assert svc.token == "jwt-2"  # noqa: S105 (test fixture, not a secret)
    assert [c[0] for c in fake.calls] == ["GET", "POST", "GET"]


async def test_fetch_message_detail(monkeypatch):
    detail = {
        "id": "m1",
        "subject": "Code",
        "from": {"address": "n@example.com", "name": ""},
        "to": [{"address": "x@mail.tm", "name": ""}],
        "intro": "123456",
        "text": "Your code is 123456",
        "html": "<p>Your code is 123456</p>",
        "seen": False,
        "createdAt": "2026-10-30T10:00:00Z",
    }
    _patch([(200, detail)], monkeypatch)
    svc = DisposableEmailService(_cfg())
    res = await svc.fetch_message("INBOX", "m1")
    assert res["success"] is True
    assert res["text_body"] == "Your code is 123456"
    assert res["to"] == ["x@mail.tm"]


async def test_connection_ok(monkeypatch):
    _patch([(200, {"address": "x@mail.tm", "id": "a1"})], monkeypatch)
    svc = DisposableEmailService(_cfg())
    res = await svc.test_connection()
    assert res["success"] is True and res["connected"] is True and res["address"] == "x@mail.tm"


def test_factory_creates_disposable():
    svc = EmailServiceFactory.create_service(_cfg())
    assert isinstance(svc, DisposableEmailService)
