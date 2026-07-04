# Quick Start

## Prerequisites
- [uv](https://docs.astral.sh/uv/) installed (recommended) or Python 3.12+
- An email account with SMTP/IMAP access

## Run Immediately

```bash
uvx email-mcp
```

## Claude Desktop (MCPB Package)

For one-click installation in Claude Desktop:

```powershell
# Build the MCPB package
uv run python build_mcpb.py
# Output: dist/email-mcp.mcpb
```

Then drag and drop `dist/email-mcp.mcpb` into Claude Desktop's MCP Servers settings page. Configure your email credentials in the server config dialog.

## Claude Desktop (Manual JSON)

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "email-mcp": {
      "command": "uv",
      "args": ["--directory", "/path/to/email-mcp", "run", "email-mcp"]
    }
  }
}
```

## Web Dashboard

Start the full web interface:

```powershell
.\start.ps1
```

Access at `http://localhost:10812`. The backend runs on port 10813.

## Configure Your Email

### Quick SMTP/IMAP

```bash
set SMTP_SERVER=smtp.gmail.com
set SMTP_PORT=587
set SMTP_USER=your.email@gmail.com
set SMTP_PASSWORD=your-app-password
```

Then restart the server. For full setup guides, see:

| Provider | Guide |
|----------|-------|
| Gmail | [docs/gmail.md](gmail.md) |
| Outlook | [docs/outlook.md](outlook.md) |
| ProtonMail | [docs/protonmail.md](protonmail.md) |
| SendGrid / Mailgun | [docs/api-services.md](api-services.md) |
| MailHog / Local | [docs/local-testing.md](local-testing.md) |
| Slack / Discord | [docs/webhook-integrations.md](webhook-integrations.md) |

## Mail Watcher

Monitor your inbox for new mail and get notified via webhook:

```powershell
# Start watching default INBOX every 60s, POST to robofang
curl -X POST http://localhost:10813/api/watcher/start `
  -H "Authorization: Basic sandra:vienna2026" `
  -H "Content-Type: application/json" `
  -d '{"interval":60,"webhook_url":"http://localhost:10956/api/alerts"}'
```

See [docs/mail-watcher.md](mail-watcher.md) and [docs/robofang-integration.md](robofang-integration.md) for detailed setup.

## Running Tests

```powershell
# All backend tests (69)
.venv\Scripts\pytest.exe tests/ -q

# Playwright e2e tests (17)
cd webapp
npx playwright test
cd ..

# Full suite: 86 tests
```

Test categories:
| Category | Count | What it covers |
|----------|-------|----------------|
| `test_sanitize.py` | 27 | Prompt injection defense (Unicode strip + safety wrap) |
| `test_api_services.py` | 17 | Service CRUD via REST API |
| `test_contacts.py` | 16 | Contact CRUD, CSV/vCard import, search |
| `test_mailing_lists.py` | 5 | Mailing list preset loading |
| `test_e2e_real.py` | 1 | Real aiosmtpd send-and-receive |
| `test_connection.py` | 2 | SMTP/IMAP connection (requires env vars) |
| **Playwright e2e** | **17** | Dashboard, inbox, compose, services, settings, chat, lab, contacts, help, sidebar, topbar, REST API |

## Available MCP Tools

| Tool | What it does |
|------|-------------|
| `send_email` | Send via any configured service |
| `check_inbox` | Read emails via IMAP |
| `email_status` | Test service connectivity |
| `list_services` | List all configured email services |
| `configure_service` | Add a new service at runtime |
| `search_emails` | Full-text search via IMAP |
| `fetch_email_detail` | Get full email body with HTML |
| `delete_email` | Remove an email |
| `mark_email_read` | Mark as read |
| `remove_service` | Remove a runtime service |
| `email_help` | Usage help and documentation |
| `mailing_lists_catalog` | List newsletter presets |
| `mailing_list_latest` | Fetch latest from a preset |
| `suggest_email_subject` | AI subject line suggestions |
| `email_agentic_assist` | Multi-step email workflow plans |

## Mail Lab (Throwaway SMTP Server)

Start a local SMTP server for testing from the web dashboard at `/lab`:

1. Go to **Mail Lab** in the sidebar
2. Click **Start** to launch a real aiosmtpd SMTP server on a free port
3. Use the **AI Message Generator** to populate the inbox with realistic test emails (10 scenarios)
4. Capture emails appear in real-time -- click to expand full body
5. **Forward** captured emails to your real email address via configured services

Or start from the CLI: `just lab`

## Common Tasks

**Send an email:**
> "Send an email to user@example.com with subject 'Hello' and body 'Test message'"

**Check unread mail:**
> "Check my inbox and show the last 10 unread emails"

**Configure a new service:**
> "Add SendGrid as a new email service with my API key"
