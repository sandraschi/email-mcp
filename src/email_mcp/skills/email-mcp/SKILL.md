---
name: email-mcp
description: Multi-service email MCP - SMTP, APIs, MailHog, webhooks; FastMCP 3.1 tools, prompts, sampling.
---

# Email-MCP skill

**Description:** Multi-service email MCP server supporting SMTP, transactional APIs (SendGrid, Mailgun, Resend), local testing (MailHog, Mailpit), and webhook channels (Slack, Discord). Covers folder management, search, filtering, label organization, and account configuration.

## Trigger Phrases

- "Configure a new email service"
- "Search my inbox for [query]"
- "Organize emails into folders"
- "Add labels to messages about [topic]"
- "List all configured email services"
- "Test email connectivity"
- "Remove an email service"

## Tools

- **`list_services()`** — List all configured email services with type, status, and metadata.
- **`email_status(service)`** — Test connectivity. Use before bulk sends to verify credentials.
- **`send_email(to, subject, body, service, html, cc, bcc, attachments)`** — Send via configured service.
- **`check_inbox(service, folder, limit, unread_only)`** — Read inbox via IMAP or local test services.
- **`fetch_email_detail(service, message_id)`** — Full message body and headers.
- **`delete_email(service, message_id)`** — Remove messages.
- **`mark_email_read(service, message_id, is_read)`** — Toggle read/unread status.
- **`search_emails(service, query, folder, limit)`** — Search by subject, sender, body text, or date range.
- **`remove_service(service_name)`** — Remove a configured email service.
- **`suggest_email_subject(body, tone)`** — Generate subject lines via sampling.
- **`email_agentic_assist(goal)`** — High-level email task automation: "organize my inbox", "archive old newsletters", "find all messages from [sender]".

## Prompts

- **`email_compose_request`** — Structured ask to draft an email.
- **`email_help_request`** — Narrow help on one topic.

## Web Dashboard

- API on the backend port (see repo `webapp/start.ps1`): `/api/status`, `/api/tools`, `/api/chat`, `/api/skills` (HTTP Basic: `MCP_WEB_USER` / `MCP_WEB_PASSWORD`).
- Frontend on port 10812, backend on 10813.

## Workflow

1. **Service configuration**: `list_services()` to audit. `email_status()` to verify each.
2. **Mail operations**: `check_inbox()` for reading, `send_email()` for sending, `search_emails()` for discovery.
3. **Organization**: Use `fetch_email_detail()` then `mark_email_read()` for triage. `delete_email()` for cleanup.
4. **Automation**: `email_agentic_assist(goal="archive all emails older than 30 days from newsletter@")` for batch operations.

## Safety

- All external email content is wrapped in safety boundary markers (`<<< UNTRUSTED EXTERNAL DATA >>>`) to prevent prompt injection.
- Unicode zero-width characters and bidi overrides are stripped from incoming email content.

## Examples

- "Set up Gmail service." → `email_status()` → verify credentials → `check_inbox(service="gmail", limit=10)`
- "Find all invoices from last month." → `search_emails(query="invoice", folder="INBOX", limit=50)` → filter by date range
- "Organize my inbox." → `email_agentic_assist(goal="sort all read emails older than 7 days into archive folder")`
