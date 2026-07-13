# Email MCP Server

<p align="center">
  <a href="https://github.com/casey/just"><img src="https://img.shields.io/badge/just-ready_to_go-7c5cfc?style=flat-square&logo=just&logoColor=white" alt="Just"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.13+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="tests/"><img src="https://img.shields.io/badge/tests-144%20passing-brightgreen?style=flat-square" alt="Tests"></a>
  <a href="https://biomejs.dev"><img src="https://img.shields.io/badge/Linted_with-Biome-60a5fa?style=flat-square&logo=biome&logoColor=white" alt="Biome"></a>
  <a href="https://github.com/PrefectHQ/fastmcp"><img src="https://img.shields.io/badge/FastMCP-3.2-7c5cfc?style=flat-square" alt="FastMCP"></a>
</p>

A full-featured email server for MCP clients. Send and receive mail through SMTP/IMAP, transactional APIs (SendGrid, Mailgun, Resend), local test servers (MailHog), and webhooks (Slack, Discord). Includes a web dashboard with AI-assisted compose, a throwaway SMTP lab, folder management, contact import, background mail watching, and creative AI workflows (love letters, complaints, ASCII art, SVG cards).

**v0.4.1** -- 144 tests passing, 32+ MCP tools, FastMCP 3.2+, dual transport (stdio + HTTP).

---

## Quick Start

```powershell
.\start.ps1
```

Opens the web dashboard at `http://localhost:10812`. Backend runs on port 10813.

**Requirements**: Python 3.12+, [uv](https://docs.astral.sh/uv/). Start configuring services from the Settings page.

For Claude Desktop setup, MCPB packaging, and manual configuration see [docs/quickstart.md](docs/quickstart.md).

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
| [docs/mail-watcher.md](docs/mail-watcher.md) | Background IMAP polling + webhook notifications |
| [docs/robofang-integration.md](docs/robofang-integration.md) | Integrate with robofang for TTS/light alerts |
| [docs/gmail.md](docs/gmail.md) | Gmail app password setup |
| [docs/outlook.md](docs/outlook.md) | Outlook/Hotmail SMTP/IMAP |
| [docs/protonmail.md](docs/protonmail.md) | ProtonMail Bridge & direct access |
| [docs/api-services.md](docs/api-services.md) | SendGrid, Mailgun, Resend, SES |
| [docs/local-testing.md](docs/local-testing.md) | MailHog, Mailpit for dev |
| [docs/webhook-integrations.md](docs/webhook-integrations.md) | Slack, Discord, Telegram |

## Features

- **32+ MCP tools**: send, receive, search, delete, mark-read, manage email services, contacts, auto-respond, workflows, mail lab
- **Web dashboard**: full React SPA at `localhost:10812`
- **AI assistant**: natural language email commands (Ollama, OpenAI, Anthropic, Google)
- **AI Improve**: rewrite email body with style/length/mood controls
- **AI Assist**: describe a service in plain language, LLM fills the config form
- **Auto-Respond**: rule-based + AI-powered auto-reply with spam detection and spoof mode
- **Bulk Send**: paste email lists with rate limiting and anti-spam safeguards
- **Dual transport**: stdio (Claude Desktop) + HTTP streamable (web)
- **Draft management**: save/compose/send from the webapp
- **Toast notifications**: live feedback for all actions
- **Prompt injection defense**: two-layer sanitization (Unicode stripping + safety boundary wrapping)
- **Mail Lab**: throwaway SMTP server for testing with AI-generated messages
- **Mail Watcher**: background IMAP polling with webhook notifications for robofang/fleet-agent integration
- **Contact import**: CSV, vCard, Google People API, Microsoft Graph API + curated lists (US Congress, EU, Austria)
- **Creative Workflows**: 7 AI letter presets with ASCII art and SVG card output
- **Folder management**: create, rename, delete IMAP folders from the webapp
- **Quick Setup**: one-click Gmail/Outlook/Yahoo/iCloud/ProtonMail/Zoho/GMX/Fastmail with email+password

## Web Dashboard

| Page | Route | Purpose |
|------|-------|---------|
| Dashboard | `/` | KPI cards, recent activity, service health |
| Inbox | `/inbox` | Read, filter, delete, auto-refresh |
| Email Detail | `/email` | Full email with HTML body, reply/delete |
| Compose | `/compose` | Send with drafts, HTML toggle, AI Improve, AI subject, Expander, Bulk Send |
| Search | `/search` | Full-text IMAP search |
| AI Chat | `/chat` | Natural language email assistant with creative workflows |
| Mail Lab | `/lab` | Throwaway SMTP server, AI message generator, mail watcher |
| Contacts | `/contacts` | Import CSV/vCard/Google/Office 365, search, groups, curated lists |
| Auto-Reply | `/auto-respond` | Rule-based + AI auto-reply, spam detection, spoof mode, pending approval |
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
| `mark_email_read` / `mark_email_unread` | Toggle read status |
| `email_status` | Test connectivity |
| `list_services` | List configured services |
| `configure_service` / `remove_service` | Manage services |
| `quick_setup` | One-click Gmail/Outlook/Yahoo/iCloud |
| `list_folders` / `create_folder` / `delete_folder` / `rename_folder` | IMAP folder CRUD |
| `email_help` | Usage help and documentation |
| `mailing_lists_catalog` | List newsletter presets |
| `mailing_list_latest` | Fetch from a preset |
| `suggest_email_subject` | AI subject line (sampling) |
| `email_agentic_assist` | Multi-step email plan |
| `add_contact` / `search_contacts` | Contact management |
| `start_watcher` / `stop_watcher` / `watcher_status` | Background IMAP polling |
| `run_workflow` | Creative email generation |
| `add_auto_rule` / `list_auto_rules` / `delete_auto_rule` | Auto-respond rules |
| `list_pending_replies` / `approve_reply` / `auto_respond_now` | Pending reply management |

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

Requires [Rust](https://rustup.rs), [Node.js 20+](https://nodejs.org), and Visual Studio Build Tools (for C++ compilation). The backend is compiled via PyInstaller and bundled as a Tauri sidecar -- no Python runtime needed.

## Development

```powershell
# Install all dependencies
uv sync --extra test --extra dev

# Start the web dashboard
.\start.ps1

# Run all backend tests
.venv\Scripts\pytest.exe tests -q

# Run Playwright e2e tests
cd webapp && npx playwright test && cd ..

# Full test suite
.venv\Scripts\pytest.exe tests -q && cd webapp && npx playwright test && cd ..

# Build MCPB package
uv run python build_mcpb.py

# Lint
uv run ruff check src
```

See [docs/quickstart.md](docs/quickstart.md) for full setup guide.

## License

MIT
