# email-mcp — Claude Code Guide

## Overview
Multi-service email platform supporting SMTP/IMAP, SendGrid, Mailgun, Resend, local testing, and webhook integrations (FastMCP 3.2, Prefab UI)

## Entry Points
- `uv run email-mcp` → `email_mcp.server:main`

## Standards
- FastMCP 3.2+ portmanteau tool pattern — tools use `operation` enum param
- Responses: structured dicts with `success`, `message`, domain-specific fields
- Dual transport: stdio (Claude Desktop) + HTTP (`MCP_TRANSPORT=http`)
- See [mcp-central-docs](https://github.com/sandraschi/mcp-central-docs) for fleet-wide coding standards

## Key Files
- `README.md` — full documentation
- `pyproject.toml` — build config and entry points
- `AGENTS.md` — OpenAI Codex agent context (if present)
