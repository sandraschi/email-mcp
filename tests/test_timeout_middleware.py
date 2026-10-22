"""Timeout guard tests: no tool may hang past the host budget (BUG-062).

Verifies ToolTimeoutMiddleware returns a dialogic timeout payload instead of
hanging, and passes fast results through untouched. Network-free.
"""

import asyncio
from types import SimpleNamespace

from fastmcp.tools.base import ToolResult

from email_mcp.sanitize import timeout_response
from email_mcp.timeout_middleware import ToolTimeoutMiddleware


def _ctx(name="check_inbox", args=None):
    return SimpleNamespace(message={"params": {"name": name, "arguments": args or {}}})


async def test_timeout_returns_dialogic_payload():
    mw = ToolTimeoutMiddleware(timeout_s=0.2)

    async def hangs(ctx):
        await asyncio.sleep(30)
        return {"success": True}  # pragma: no cover - never reached

    res = await mw.on_call_tool(_ctx(), hangs)
    assert isinstance(res, ToolResult)
    assert res.is_error is True
    payload = res.structured_content
    assert payload["success"] is False
    assert payload["error_type"] == "timeout"
    assert "check_inbox" in payload["error"]
    assert isinstance(payload["message"], str) and payload["message"]
    assert isinstance(payload["suggestions"], list) and payload["suggestions"]
    assert isinstance(payload["recovery_options"], list) and payload["recovery_options"]
    dlg = payload["dialogic"]
    assert dlg["suggestion"] and dlg["remediation"]
    assert dlg["context_dump"]["tool"] == "check_inbox"


async def test_fast_tool_passes_through():
    mw = ToolTimeoutMiddleware(timeout_s=5.0)

    async def fast(ctx):
        return {"success": True, "count": 3}

    res = await mw.on_call_tool(_ctx("list_services"), fast)
    assert res == {"success": True, "count": 3}


async def test_timeout_response_shape_standalone():
    payload = timeout_response("search_emails", 50.0, service="gmail")
    assert payload["success"] is False
    assert payload["error_type"] == "timeout"
    assert payload["dialogic"]["context_dump"] == {
        "tool": "search_emails",
        "timeout_s": 50.0,
        "service": "gmail",
    }
