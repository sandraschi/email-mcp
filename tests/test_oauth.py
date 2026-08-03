"""Tests for the OAuth2 (XOAUTH2) module."""

from __future__ import annotations

import base64
import json
import time

import pytest

from email_mcp import oauth


def test_build_xoauth2():
    s = oauth.build_xoauth2("user@example.com", "tok123")
    assert s == "user=user@example.com\x01auth=Bearer tok123\x01\x01"


def test_account_from_id_token():
    claims = {"preferred_username": "sandra@hotmail.com", "email": "sandra@hotmail.com"}
    payload = base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip("=")
    token = f"header.{payload}.sig"
    assert oauth._account_from_id_token(token) == "sandra@hotmail.com"


def test_account_from_id_token_empty():
    assert oauth._account_from_id_token("") == ""
    assert oauth._account_from_id_token("not.a.jwt") == ""


def test_token_store_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("EMAIL_MCP_OAUTH_TOKEN_FILE", str(tmp_path / "tokens.json"))
    token = oauth.OAuthToken(
        account="a@example.com",
        access_token="acc",
        refresh_token="ref",
        scope="s",
        expires_at=time.time() + 3600,
    )
    oauth.save_token(token)
    loaded = oauth.get_token("a@example.com")
    assert loaded is not None
    assert loaded.access_token == "acc"
    # case-insensitive lookup
    assert oauth.has_token("A@EXAMPLE.COM")


def test_get_token_refreshes_when_expired(tmp_path, monkeypatch):
    monkeypatch.setenv("EMAIL_MCP_OAUTH_TOKEN_FILE", str(tmp_path / "tokens.json"))
    monkeypatch.setenv("EMAIL_MCP_OAUTH_CLIENT_ID", "client-1")
    token = oauth.OAuthToken(
        account="a@example.com",
        access_token="old",
        refresh_token="ref",
        scope="s",
        expires_at=time.time() - 10,
    )
    oauth.save_token(token)

    called = {}

    def fake_post(url, data, timeout=60.0):
        called["url"] = url
        called["grant"] = data.get("grant_type")
        return {
            "access_token": "new",
            "refresh_token": "ref2",
            "expires_in": 3600,
            "scope": "s",
        }

    monkeypatch.setattr(oauth, "_post", fake_post)
    refreshed = oauth.get_token("a@example.com")
    assert refreshed is not None
    assert refreshed.access_token == "new"
    assert called["grant"] == "refresh_token"
    assert refreshed.account == "a@example.com"
    # persisted
    assert oauth.get_token("a@example.com").access_token == "new"


def test_get_token_refreshes_with_tokens_own_scope(tmp_path, monkeypatch):
    """Refreshing a graph token must request graph scopes (family-preserving)."""
    monkeypatch.setenv("EMAIL_MCP_OAUTH_TOKEN_FILE", str(tmp_path / "tokens.json"))
    monkeypatch.setenv("EMAIL_MCP_OAUTH_CLIENT_ID", "client-1")
    token = oauth.OAuthToken(
        account="a@example.com",
        access_token="old",
        refresh_token="ref",
        scope=oauth.GRAPH_SCOPE,
        expires_at=time.time() - 10,
    )
    oauth.save_token(token)

    seen = {}

    def fake_post(url, data, timeout=60.0):
        seen["scope"] = data.get("scope")
        return {
            "access_token": "new",
            "refresh_token": "ref2",
            "scope": oauth.GRAPH_SCOPE,
            "expires_in": 3600,
        }

    monkeypatch.setattr(oauth, "_post", fake_post)
    loaded = oauth.get_token("a@example.com", oauth.GRAPH_SCOPE)
    assert loaded is not None
    assert loaded.access_token == "new"
    assert "graph.microsoft.com" in (seen["scope"] or "")
    assert oauth.has_token("a@example.com", oauth.GRAPH_SCOPE)


def test_token_file_tauri_mode(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setenv("EMAIL_MCP_TAURI", "1")
    monkeypatch.delenv("EMAIL_MCP_OAUTH_TOKEN_FILE", raising=False)
    assert oauth.token_file() == tmp_path / "ai.fleet.email-mcp" / "oauth_tokens.json"


def test_token_file_dev_default(monkeypatch):
    monkeypatch.delenv("EMAIL_MCP_TAURI", raising=False)
    monkeypatch.delenv("EMAIL_MCP_OAUTH_TOKEN_FILE", raising=False)
    p = oauth.token_file()
    assert p.name == "oauth_tokens.json"
    assert "data" in p.parts


def test_start_device_flow_requires_client_id(monkeypatch):
    monkeypatch.delenv("EMAIL_MCP_OAUTH_CLIENT_ID", raising=False)
    result = oauth.start_device_flow(cid=None)
    assert result["success"] is False
    assert "CLIENT_ID" in result["error"]


def test_start_device_flow_ok(monkeypatch):
    def fake_post(url, data, timeout=60.0):
        return {
            "device_code": "dc",
            "user_code": "ABC-DEF",
            "verification_uri": "https://microsoft.com/devicelogin",
            "expires_in": 900,
            "interval": 5,
        }

    monkeypatch.setattr(oauth, "_post", fake_post)
    result = oauth.start_device_flow(cid="client-1")
    assert result["success"] is True
    assert result["user_code"] == "ABC-DEF"


def test_poll_device_flow_pending(monkeypatch):
    import httpx

    def fake_post(url, data, timeout=60.0):
        resp = httpx.Response(400, json={"error": "authorization_pending"})
        raise httpx.HTTPStatusError("pending", request=httpx.Request("POST", url), response=resp)

    monkeypatch.setattr(oauth, "_post", fake_post)
    assert oauth.poll_device_flow("dc", cid="client-1")["status"] == "pending"


def test_poll_device_flow_authorized(tmp_path, monkeypatch):
    monkeypatch.setenv("EMAIL_MCP_OAUTH_TOKEN_FILE", str(tmp_path / "tokens.json"))
    claims = {"preferred_username": "sandra@hotmail.com"}
    payload = base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip("=")
    id_token = f"h.{payload}.s"

    def fake_post(url, data, timeout=60.0):
        return {
            "access_token": "acc",
            "refresh_token": "ref",
            "expires_in": 3600,
            "scope": "s",
            "id_token": id_token,
        }

    monkeypatch.setattr(oauth, "_post", fake_post)
    result = oauth.poll_device_flow("dc", cid="client-1")
    assert result["status"] == "authorized"
    assert result["account"] == "sandra@hotmail.com"
    assert oauth.has_token("sandra@hotmail.com")


def test_authenticate_imap_falls_back_without_token(tmp_path, monkeypatch):
    monkeypatch.setenv("EMAIL_MCP_OAUTH_TOKEN_FILE", str(tmp_path / "tokens.json"))
    monkeypatch.setenv("EMAIL_MCP_OAUTH_CLIENT_ID", "client-1")

    class FakeMail:
        def __init__(self):
            self.authenticated = False

        def authenticate(self, mech, cb):
            raise AssertionError("should not be called without a token")

    mail = FakeMail()
    # no token -> returns False (caller falls back to password)
    assert oauth.authenticate_imap(mail, "a@example.com") is False


def test_authenticate_imap_with_token(monkeypatch, tmp_path):
    monkeypatch.setenv("EMAIL_MCP_OAUTH_TOKEN_FILE", str(tmp_path / "tokens.json"))
    token = oauth.OAuthToken(
        account="a@example.com",
        access_token="acc",
        refresh_token="ref",
        scope="s",
        expires_at=time.time() + 3600,
    )
    oauth.save_token(token)

    class FakeMail:
        def __init__(self):
            self.auth_str = b""

        def authenticate(self, mech, cb):
            self.auth_str = cb(None)

    mail = FakeMail()
    assert oauth.authenticate_imap(mail, "a@example.com") is True
    assert mail.auth_str == b"user=a@example.com\x01auth=Bearer acc\x01\x01"


def test_authenticate_imap_failure_falls_back(monkeypatch, tmp_path):
    monkeypatch.setenv("EMAIL_MCP_OAUTH_TOKEN_FILE", str(tmp_path / "tokens.json"))
    token = oauth.OAuthToken(
        account="a@example.com",
        access_token="acc",
        refresh_token="ref",
        scope="s",
        expires_at=time.time() + 3600,
    )
    oauth.save_token(token)

    class FakeMail:
        def authenticate(self, mech, cb):
            raise Exception("XOAUTH2 rejected")

    assert oauth.authenticate_imap(FakeMail(), "a@example.com") is False


@pytest.mark.parametrize("account", ["", None])
def test_get_token_no_account(account):
    assert oauth.get_token(account) is None


def test_family_derivation():
    assert oauth._family(oauth.DEFAULT_SCOPE) == "exchange"
    assert oauth._family(oauth.GRAPH_SCOPE) == "graph"
    assert oauth._family("") == "exchange"
    assert oauth.family_scope("graph") == oauth.GRAPH_SCOPE
    assert oauth.family_scope("exchange") == oauth.DEFAULT_SCOPE


def test_exchange_and_graph_tokens_coexist(tmp_path, monkeypatch):
    monkeypatch.setenv("EMAIL_MCP_OAUTH_TOKEN_FILE", str(tmp_path / "tokens.json"))
    exchange = oauth.OAuthToken(
        account="a@example.com",
        access_token="ex-tok",
        refresh_token="ex-ref",
        scope=oauth.DEFAULT_SCOPE,
        expires_at=time.time() + 3600,
    )
    graph = oauth.OAuthToken(
        account="a@example.com",
        access_token="gr-tok",
        refresh_token="gr-ref",
        scope=oauth.GRAPH_SCOPE,
        expires_at=time.time() + 3600,
    )
    oauth.save_token(exchange)
    oauth.save_token(graph)
    assert oauth.get_token("a@example.com", oauth.DEFAULT_SCOPE).access_token == "ex-tok"
    assert oauth.get_token("a@example.com", oauth.GRAPH_SCOPE).access_token == "gr-tok"
    assert oauth.has_token("a@example.com", oauth.GRAPH_SCOPE)
    assert oauth.has_token("a@example.com", oauth.DEFAULT_SCOPE)


def test_legacy_plain_key_still_read(tmp_path, monkeypatch):
    monkeypatch.setenv("EMAIL_MCP_OAUTH_TOKEN_FILE", str(tmp_path / "tokens.json"))
    path = oauth.token_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "a@example.com": {
                    "account": "a@example.com",
                    "access_token": "legacy",
                    "refresh_token": "ref",
                    "scope": oauth.DEFAULT_SCOPE,
                    "expires_at": time.time() + 3600,
                    "obtained_at": time.time(),
                }
            }
        ),
        encoding="utf-8",
    )
    assert oauth.get_token("a@example.com", oauth.DEFAULT_SCOPE).access_token == "legacy"
