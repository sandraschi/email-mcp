"""Server-wide MCP tool timeout guard (BUG-062 class fix).

RATIONALE: a single stalled tool call (hung IMAP socket, expired OAuth refresh,
wedged provider) must never wedge the whole stdio session. Every `tools/call`
gets a hard time budget just under the host's 60 s client timeout; on expiry
the client receives a structured dialogic timeout payload (DIALOGIC_RETURNS.md
+ TOOL_DESIGN_STANDARDS.md sec 7) instead of a bare MCP -32001 timeout.

Bounds are layered so the inner failure always surfaces first:
  provider socket (IMAP 25 s / Graph 40 s / OAuth 45 s)
    < tool guard (EMAIL_MCP_TOOL_TIMEOUT, default 50 s)
      < REST guard (_safe_call 55 s)
        < host client timeout (60 s)
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

from fastmcp.server.middleware import CallNext, Middleware, MiddlewareContext
from fastmcp.tools.base import ToolResult

from email_mcp.sanitize import timeout_response

logger = logging.getLogger(__name__)

TOOL_TIMEOUT_S = float(os.getenv("EMAIL_MCP_TOOL_TIMEOUT", "50"))


def _tool_name_and_args(message: Any) -> tuple[str, dict[str, Any]]:
    """Extract (tool_name, arguments) from a tools/call message defensively.

    The message shape differs across FastMCP versions (params model vs raw
    dict vs full JSON-RPC envelope), so try each shape instead of assuming one.
    """
    if isinstance(message, dict):
        params = message.get("params", message)
        if isinstance(params, dict):
            name = params.get("name", "unknown")
            args = params.get("arguments", {})
            return str(name), args if isinstance(args, dict) else {}
        return "unknown", {}
    name = getattr(message, "name", None)
    if name is not None:
        args = getattr(message, "arguments", {}) or {}
        return str(name), args if isinstance(args, dict) else {}
    params = getattr(message, "params", None)
    if params is not None:
        return _tool_name_and_args(params)
    return "unknown", {}


class ToolTimeoutMiddleware(Middleware):
    """Bound every tool call; answer timeouts instead of hanging (BUG-062)."""

    def __init__(self, timeout_s: float = TOOL_TIMEOUT_S) -> None:
        self.timeout_s = timeout_s

    async def on_call_tool(
        self,
        context: MiddlewareContext[Any],
        call_next: CallNext[Any, Any],
    ) -> Any:
        tool_name, args = _tool_name_and_args(context.message)
        # WEBAPP_LOGS_PAGE.md §4: every tool call lands in the ring buffer
        # with kind=tool_call (INFO on success, ERROR on failure).
        extra = {"kind": "tool_call", "tool": tool_name}
        try:
            result = await asyncio.wait_for(call_next(context), timeout=self.timeout_s)
        except TimeoutError:
            logger.warning(
                "tool timeout: %s exceeded %.0fs budget - returning dialogic failure",
                tool_name,
                self.timeout_s,
                extra=extra,
            )
            payload = timeout_response(
                tool_name,
                self.timeout_s,
                service=args.get("service") if isinstance(args, dict) else None,
            )
            return ToolResult(structured_content=payload, is_error=True)
        except Exception:
            logger.exception("tool error: %s raised - returning failure", tool_name, extra=extra)
            raise
        if bool(getattr(result, "is_error", False)):
            logger.warning("tool_call %s (error)", tool_name, extra=extra)
        else:
            logger.info("tool_call %s (ok)", tool_name, extra=extra)
        return result
