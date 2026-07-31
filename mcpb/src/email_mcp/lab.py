"""MailLab -- throwaway SMTP server for testing.

Manages a real aiosmtpd SMTP server in a background thread, captures all
incoming emails, and exposes them for the web dashboard (inbox view, AI
generation, forwarding).
"""

from __future__ import annotations

import threading
import time
import uuid
from email.parser import BytesParser
from typing import Any

try:
    from aiosmtpd.controller import Controller
    from aiosmtpd.handlers import Sink
    from aiosmtpd.smtp import SMTP as SMTPServer

    HAS_AIOSMTPD = True
except ImportError:
    HAS_AIOSMTPD = False

    # Dummy types so the module still compiles
    class Sink:  # type: ignore[no-redef]
        pass

    class Controller:  # type: ignore[no-redef]
        def __init__(self, *a, **kw):
            pass

        def start(self):
            pass

        def stop(self):
            pass

    class SMTPServer:  # type: ignore[no-redef]
        pass


from .sanitize import sanitize_text

# ── In-memory captured email store ──────────────────────────────────────────

_captured: list[dict[str, Any]] = []


class _CaptureHandler(Sink):
    """SMTP handler that stores every received email."""

    async def handle_DATA(self, server: SMTPServer, session, envelope) -> str:
        raw = envelope.content
        msg = BytesParser().parsebytes(raw)
        email_id = str(uuid.uuid4())[:12]
        text_body, html_body = _parse_body(msg)
        _captured.append(
            {
                "id": email_id,
                "from": sanitize_text(envelope.mail_from or ""),
                "to": [sanitize_text(a) for a in envelope.rcpt_tos],
                "subject": sanitize_text(msg.get("Subject", "") or "(No Subject)"),
                "text_body": sanitize_text(text_body),
                "html_body": html_body,
                "date": time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime()),
                "raw_size": len(raw),
            }
        )
        return "250 OK"


def _parse_body(msg) -> tuple[str, str | None]:
    text_body = ""
    html_body: str | None = None
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            payload = part.get_payload(decode=True)
            if payload:
                charset = part.get_content_charset() or "utf-8"
                decoded = payload.decode(charset, errors="replace")
                if ct == "text/plain" and not text_body:
                    text_body = decoded
                elif ct == "text/html" and html_body is None:
                    html_body = decoded
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            text_body = payload.decode(charset, errors="replace")
        else:
            text_body = str(msg.get_payload() or "")
    return text_body, html_body


# ── SMTP server lifecycle ──────────────────────────────────────────────────

_server: Controller | None = None
_server_port: int = 0
_server_thread: threading.Thread | None = None


def start_server(port: int = 0) -> dict[str, Any]:
    """Start the throwaway SMTP server in background thread."""
    global _server, _server_port, _server_thread

    if not HAS_AIOSMTPD:
        return {
            "running": False,
            "port": 0,
            "email_count": 0,
            "error": "aiosmtpd not installed. Run: uv pip install aiosmtpd",
        }

    if _server is not None:
        return {"running": True, "port": _server_port, "email_count": len(_captured), "message": "Already running"}

    _captured.clear()
    _server = Controller(_CaptureHandler(), hostname="127.0.0.1", port=port)
    _server.start()
    try:
        svr = getattr(_server, "server", None)
        _server_port = svr.sockets[0].getsockname()[1] if svr and hasattr(svr, "sockets") and svr.sockets else port
    except Exception:
        _server_port = port or 1025
    return {
        "running": True,
        "port": _server_port,
        "email_count": 0,
        "message": f"Server started on 127.0.0.1:{_server_port}",
    }


def stop_server() -> dict[str, Any]:
    """Stop the throwaway SMTP server."""
    global _server, _server_port
    if _server is None:
        return {"running": False, "port": 0, "email_count": len(_captured), "message": "No server running"}
    _server.stop()
    _server = None
    _server_port = 0
    count = len(_captured)
    return {"running": False, "port": 0, "email_count": count, "message": f"Server stopped. {count} email(s) captured."}


def server_status() -> dict[str, Any]:
    """Get current server status."""
    return {
        "running": _server is not None,
        "port": _server_port,
        "email_count": len(_captured),
    }


def list_emails() -> list[dict[str, Any]]:
    """Return captured email summaries for the web inbox."""
    return [
        {
            "id": e["id"],
            "from": e["from"],
            "to": e["to"],
            "subject": e["subject"],
            "date": e["date"],
            "size": e["raw_size"],
        }
        for e in _captured
    ]


def get_email(email_id: str) -> dict[str, Any] | None:
    """Return full email detail by ID."""
    for e in _captured:
        if e["id"] == email_id:
            return dict(e)
    return None


def clear_emails() -> dict[str, Any]:
    """Clear all captured emails."""
    global _captured
    count = len(_captured)
    _captured = []
    return {"cleared": count, "message": f"Cleared {count} email(s)"}


# ── Inject a pre-built email (for AI generation) ────────────────────────────


def inject_email(from_addr: str, to: list[str], subject: str, text_body: str, html_body: str | None = None) -> dict[str, Any]:
    """Inject a synthetic email into the captured store as if received via SMTP.

    Used by the AI generator to populate the throwaway inbox without needing
    a real SMTP connection.
    """
    email_id = str(uuid.uuid4())[:12]
    entry = {
        "id": email_id,
        "from": sanitize_text(from_addr),
        "to": [sanitize_text(a) for a in to] if isinstance(to, list) else [sanitize_text(to)],
        "subject": sanitize_text(subject) or "(No Subject)",
        "text_body": sanitize_text(text_body),
        "html_body": html_body,
        "date": time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime()),
        "raw_size": len(text_body) + len(html_body or ""),
    }
    _captured.append(entry)
    return entry
