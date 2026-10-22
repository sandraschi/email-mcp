"""Gmail env auto-config tests (no network).

GMAIL_USER + GMAIL_APP_PASSWORD in the environment must register a "gmail"
service on startup; without them no gmail service may appear.
"""

import os

from email_mcp.server import EmailMCP

_SIBLING_KEYS = (
    "SENDGRID_API_KEY",
    "MAILGUN_API_KEY",
    "MAILGUN_DOMAIN",
    "RESEND_API_KEY",
    "MAILHOG_ENABLED",
    "SLACK_WEBHOOK_URL",
    "EMAIL_MCP_OAUTH_CLIENT_ID",
)


def _fresh(monkeypatch):
    for key in ("GMAIL_USER", "GMAIL_APP_PASSWORD", *_SIBLING_KEYS):
        monkeypatch.delenv(key, raising=False)
    inst = EmailMCP.__new__(EmailMCP)
    inst.services = {}
    return inst


def test_gmail_env_registers_service(monkeypatch):
    inst = _fresh(monkeypatch)
    monkeypatch.setenv("GMAIL_USER", "you@gmail.com")
    monkeypatch.setenv("GMAIL_APP_PASSWORD", "abcd-abcd-abcd-abcd")
    EmailMCP._load_preconfigured_services(inst)
    svc = inst.services.get("gmail")
    assert svc is not None
    assert svc.name == "gmail"
    cfg = svc.config.config
    assert cfg["imap_server"] == "imap.gmail.com"
    assert cfg["imap_port"] == 993
    assert cfg["smtp_server"] == "smtp.gmail.com"
    assert cfg["smtp_port"] == 587
    assert cfg["imap_user"] == "you@gmail.com"
    assert cfg["imap_password"] == "abcd-abcd-abcd-abcd"  # noqa: S105 - test fixture, not a secret


def test_gmail_env_absent_registers_nothing(monkeypatch):
    inst = _fresh(monkeypatch)
    EmailMCP._load_preconfigured_services(inst)
    assert "gmail" not in inst.services
    assert os.getenv("GMAIL_USER") is None


def test_gmail_needs_both_vars(monkeypatch):
    inst = _fresh(monkeypatch)
    monkeypatch.setenv("GMAIL_USER", "you@gmail.com")
    EmailMCP._load_preconfigured_services(inst)
    assert "gmail" not in inst.services
