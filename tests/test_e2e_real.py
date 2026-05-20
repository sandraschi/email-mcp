"""End-to-end test: real throwaway SMTP + HTTP server.

Spins up a real aiosmtpd SMTP server and a simple HTTP API (MailHog-compatible)
for the full send-and-read cycle. No Docker, no mocks.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import AsyncIterator
from email.parser import BytesParser
from typing import Any

import httpx
import pytest
from aiosmtpd.controller import Controller
from aiosmtpd.handlers import Sink
from aiosmtpd.smtp import SMTP as SMTPServer

from tests.conftest import AUTH_HEADER

SMTP_PORT = 11225
HTTP_PORT = 18225
SERVICE_NAME = "e2e-real"

_captured_emails: list[dict[str, Any]] = []


class CaptureHandler(Sink):
    async def handle_DATA(self, server: SMTPServer, session, envelope) -> str:
        raw = envelope.content
        msg = BytesParser().parsebytes(raw)
        _captured_emails.append(
            {
                "id": str(uuid.uuid4()),
                "from": envelope.mail_from,
                "to": envelope.rcpt_tos,
                "subject": msg.get("Subject", ""),
                "body": _decode_body(msg),
                "raw": raw,
            }
        )
        return "250 OK"


def _decode_body(msg) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    return payload.decode("utf-8", errors="replace")
                return str(part.get_payload())
    payload = msg.get_payload(decode=True)
    if payload:
        return payload.decode("utf-8", errors="replace")
    return str(msg.get_payload() or "")


async def _http_handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    request_line = (await reader.readline()).decode("utf-8", errors="replace").strip()
    while True:
        line = (await reader.readline()).decode("utf-8", errors="replace").strip()
        if not line:
            break
    method, path, _ = request_line.split(" ") if request_line else ("", "", "")
    if path == "/api/v2/messages":
        items = []
        for m in _captured_emails:
            items.append(
                {
                    "Content": {
                        "Headers": {
                            "Subject": [m["subject"]],
                            "To": m["to"],
                            "From": [m["from"]],
                        },
                        "Body": m["body"],
                    },
                }
            )
        body = json.dumps({"items": items, "count": len(items), "total": len(items)}).encode()
        resp = (
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Type: application/json\r\n"
            b"Content-Length: " + str(len(body)).encode() + b"\r\n"
            b"\r\n" + body
        )
    else:
        resp = b"HTTP/1.1 404 Not Found\r\nContent-Length: 0\r\n\r\n"
    writer.write(resp)
    await writer.drain()
    writer.close()


@pytest.fixture
async def servers() -> AsyncIterator[None]:
    """Start real SMTP + HTTP servers, yield, tear down."""
    _captured_emails.clear()
    smtp_ctrl = Controller(CaptureHandler(), hostname="127.0.0.1", port=SMTP_PORT)
    smtp_ctrl.start()

    http_srv = await asyncio.start_server(_http_handler, "127.0.0.1", HTTP_PORT)

    yield

    smtp_ctrl.stop()
    http_srv.close()


@pytest.mark.slow
@pytest.mark.integration
class TestRealE2E:
    async def test_send_and_receive(
        self,
        client: httpx.AsyncClient,
        servers: None,
    ) -> None:
        _captured_emails.clear()
        test_to = "recipient@e2e-test.com"
        test_subject = "E2E Real Server Test"
        test_body = "This email was sent through a real throwaway SMTP server."

        svc_payload = {
            "name": SERVICE_NAME,
            "type": "local",
            "config": {
                "smtp_server": "127.0.0.1",
                "smtp_port": SMTP_PORT,
                "http_url": f"http://127.0.0.1:{HTTP_PORT}",
                "service_type": "mailhog",
            },
        }

        try:
            r = await client.post("/api/services", json=svc_payload, headers={"Authorization": AUTH_HEADER})
            assert r.status_code == 200
            assert r.json().get("success") is True

            send_resp = await client.post(
                "/api/send",
                json={"to": test_to, "subject": test_subject, "body": test_body, "service": SERVICE_NAME},
                headers={"Authorization": AUTH_HEADER},
            )
            send_data = send_resp.json()
            assert send_data.get("success") is True, f"Send failed: {send_data}"

            assert len(_captured_emails) >= 1, "No email captured"
            captured = _captured_emails[-1]
            assert captured["subject"] == test_subject
            assert test_to in captured["to"]
            assert test_body in captured["body"]

            print(f"\n  OK - Email verified: {test_subject!r} -> {test_to}")

        finally:
            await client.delete(f"/api/services/{SERVICE_NAME}", headers={"Authorization": AUTH_HEADER})
