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
4. Capture emails appear in real-time — click to expand full body
5. **Forward** captured emails to your real email address via configured services

Or start from the CLI: `just lab`

## Common Tasks

**Send an email:**
> "Send an email to user@example.com with subject 'Hello' and body 'Test message'"

**Check unread mail:**
> "Check my inbox and show the last 10 unread emails"

**Configure a new service:**
> "Add SendGrid as a new email service with my API key"
