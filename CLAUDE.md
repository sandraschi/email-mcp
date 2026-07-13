# email-mcp -- Claude Code Guide

## Overview
Multi-service email platform supporting SMTP/IMAP, SendGrid, Mailgun, Resend, local testing, and webhook integrations (FastMCP 3.2, Prefab UI)

## Entry Points
- `uv run email-mcp` → `email_mcp.server:main`

## Standards
- FastMCP 3.2+ portmanteau tool pattern -- tools use `operation` enum param
- Responses: structured dicts with `success`, `message`, domain-specific fields
- Dual transport: stdio (Claude Desktop) + HTTP (`MCP_TRANSPORT=http`)
- See [mcp-central-docs](https://github.com/sandraschi/mcp-central-docs) for fleet-wide coding standards

## Session Context
- **Before starting work**: call `email_status()` to check connectivity, then `check_inbox(service="default", unread_only=True, limit=10)` for recent activity
- **At end of work**: send drafted emails, mark read, subscribe to mailing lists via `mailing_list_latest()`

## Key Files
- `README.md` -- full documentation
- `pyproject.toml` -- build config and entry points
- `AGENTS.md` -- Agent context
