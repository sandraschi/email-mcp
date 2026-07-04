# email-mcp -- Project Assessment

**Category**: MCP Server + Email Platform
**Assessment Date**: 2026-06-27
**Version**: 0.4.1

---

## Summary

| Metric | Value |
|--------|-------|
| Status | Stable + Active Development |
| MCP Tools | 32+ (15 core + folder CRUD + watcher + contacts + auto-respond + creative workflows) |
| Tests | 86 (69 backend pytest + 17 Playwright e2e) |
| Framework | FastMCP 3.2+, FastAPI, React 19 |
| Security | Two-layer prompt injection defense |
| AI Integration | Multi-provider (Ollama, OpenAI, Anthropic, Google, LM Studio) |

---

## Features

- Multi-service email (SMTP/IMAP, SendGrid, Mailgun, Resend, SES, webhooks)
- Web dashboard with AI-assisted compose, inbox management, contacts
- Auto-respond engine with rule matching, spam detection, spoof mode
- Mail Watcher: background IMAP polling with webhook POST
- Mail Lab: throwaway aiosmtpd SMTP server
- Contact import (CSV, vCard, Google People, Microsoft Graph, curated official lists)
- Creative AI workflows (7 presets with text/ASCII/SVG output)
- Folder management (CRUD IMAP folders)
- Scheduled send, drafts, signatures, templates
- Bulk send with rate limiting
- Dual transport: stdio + HTTP streamable
- Tauri 2.0 native desktop app

---

## Code Quality
- Ruff linting (line-length 230, py312 target)
- JSON file-based persistence
- Structured logging (structlog)
- No external database dependency

---

## Docs
- [README.md](README.md) -- full feature overview and quick start
- [docs/](docs/) -- 11 sub-documents covering setup, configuration, providers
