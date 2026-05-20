"""Pytest fixtures for Email-MCP API tests."""

from __future__ import annotations

import base64
from collections.abc import AsyncIterator

import httpx
import pytest

from email_mcp.server import app

AUTH_USER = "sandra"
AUTH_PASS = "vienna2026"
AUTH_HEADER = f"Basic {base64.b64encode(f'{AUTH_USER}:{AUTH_PASS}'.encode()).decode()}"


@pytest.fixture
async def client() -> AsyncIterator[httpx.AsyncClient]:
    """FastAPI test client via ASGI transport."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
def auth() -> dict[str, str]:
    """HTTP Basic auth header."""
    return {"Authorization": AUTH_HEADER}


@pytest.fixture
def smtp_config() -> dict:
    """A valid SMTP service configuration for testing."""
    return {
        "smtp_server": "smtp.example.com",
        "smtp_port": 587,
        "smtp_user": "test@example.com",
        "smtp_password": "test-password",
    }


@pytest.fixture
def mailhog_config() -> dict:
    """A valid MailHog/local service configuration for testing."""
    return {
        "smtp_server": "localhost",
        "smtp_port": 1025,
        "http_url": "http://localhost:8025",
        "service_type": "mailhog",
    }
