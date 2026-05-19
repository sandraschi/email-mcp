# MiniMail MCP Server

[![FastMCP Version](https://img.shields.io/badge/FastMCP-3.1.0-blue?style=flat-square)](https://github.com/sandraschi/fastmcp)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Linted with Biome](https://img.shields.io/badge/Linted_with-Biome-60a5fa?style=flat-square)](https://biomejs.dev/)

Multi-service email platform for MCP clients. Send and receive email via SMTP/IMAP, transactional APIs, local test servers, and webhooks.

**v0.4.0** — FastMCP 3.2+, web dashboard, AI assistant, mailing list presets, prompt injection defense.

---

## Quick Start

```powershell
# Start the web dashboard
.\start.ps1
# Open http://localhost:10812
```

```
uvx email-mcp  # CLI mode
```

See [docs/quickstart.md](docs/quickstart.md) for full setup.

## Supported Email Systems

| Type | Providers | Guide |
|------|-----------|-------|
| **SMTP/IMAP** | Gmail, Outlook, Yahoo, iCloud, ProtonMail | [docs/gmail.md](docs/gmail.md), [docs/outlook.md](docs/outlook.md), [docs/protonmail.md](docs/protonmail.md) |
| **Transactional APIs** | SendGrid, Mailgun, Resend, Amazon SES | [docs/api-services.md](docs/api-services.md) |
| **Local Testing** | MailHog, Mailpit, MailCatcher, Inbucket | [docs/local-testing.md](docs/local-testing.md) |
| **Webhooks** | Slack, Discord, Telegram | [docs/webhook-integrations.md](docs/webhook-integrations.md) |

## Documentation

| Document | Contents |
|----------|----------|
| [docs/quickstart.md](docs/quickstart.md) | Installation, Claude Desktop setup, first email |
| [docs/configuration.md](docs/configuration.md) | All env vars, mailing lists, dynamic config |
| [docs/safety-hardening.md](docs/safety-hardening.md) | Prompt injection defense architecture |
| [docs/gmail.md](docs/gmail.md) | Gmail app password setup |
| [docs/outlook.md](docs/outlook.md) | Outlook/Hotmail SMTP/IMAP |
| [docs/protonmail.md](docs/protonmail.md) | ProtonMail Bridge & direct access |
| [docs/api-services.md](docs/api-services.md) | SendGrid, Mailgun, Resend, SES |
| [docs/local-testing.md](docs/local-testing.md) | MailHog, Mailpit for dev |
| [docs/webhook-integrations.md](docs/webhook-integrations.md) | Slack, Discord, Telegram |

## Features

- **15 MCP tools**: send, receive, search, delete, mark-read, manage email services
- **Web dashboard**: full React SPA at `localhost:10812`
- **AI assistant**: natural language email commands (Ollama, OpenAI, Anthropic, Google)
- **AI Improve**: rewrite email body with style/length/mood controls
- **AI Assist**: describe a service in plain language, LLM fills the config form
- **Dual transport**: stdio (Claude Desktop) + HTTP streamable (web)
- **Draft management**: save/compose/send from the webapp
- **Toast notifications**: live feedback for all actions
- **Prompt injection defense**: two-layer sanitization (Unicode stripping + safety boundary wrapping)
- **Structured logging**: JSON output via structlog

## Web Dashboard

| Page | Route | Purpose |
|------|-------|---------|
| Dashboard | `/` | KPI cards, recent activity, service health |
| Inbox | `/inbox` | Read, filter, delete, auto-refresh |
| Email Detail | `/email` | Full email with HTML body, reply/delete |
| Compose | `/compose` | Send with drafts, HTML toggle, AI Improve, AI subject |
| Search | `/search` | Full-text IMAP search |
| AI Chat | `/chat` | Natural language email assistant |
| Services | `/services` | Form-based add/remove/test with AI Assist presets |
| Tools | `/tools` | Execute MCP tools from the browser |
| Settings | `/settings` | AI provider config, email credentials |
| Help | `/help` | Tabbed documentation (6 tabs) |

## Tools

| Tool | Description |
|------|-------------|
| `send_email` | Send via any service |
| `check_inbox` | Read IMAP inbox |
| `fetch_email_detail` | Get full email with body |
| `search_emails` | IMAP full-text search |
| `delete_email` | Remove email (IMAP) |
| `mark_email_read` | Mark as read |
| `email_status` | Test connectivity |
| `list_services` | List configured services |
| `configure_service` | Add service at runtime |
| `remove_service` | Remove a service |
| `mailing_lists_catalog` | List newsletter presets |
| `mailing_list_latest` | Fetch from a preset |
| `suggest_email_subject` | AI subject line (sampling) |
| `email_agentic_assist` | Multi-step email plan |

## Ports

| Service | Port |
|---------|------|
| Web dashboard frontend | 10812 |
| Backend API + MCP HTTP | 10813 |

## Native Desktop App (Tauri 2.0)

A standalone Windows desktop app is available, bundling the webapp + Python backend into a single installer (~15 MB).

```powershell
# Build everything in one command:
just build-native

# Installer lands at:
# native/target/release/bundle/nsis/Email MCP_0.1.0_x64-setup.exe
```

Requires [Rust](https://rustup.rs), [Node.js 20+](https://nodejs.org), and Visual Studio Build Tools (for C++ compilation). The backend is compiled via PyInstaller and bundled as a Tauri sidecar — no Python runtime needed.

## Development

```powershell
uv sync --extra test --extra dev
uv run ruff check src tests
# See docs/quickstart.md for full dev guide
```

## License

MIT
