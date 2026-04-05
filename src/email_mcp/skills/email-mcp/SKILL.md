---
name: email-mcp
description: Multi-service email MCP - SMTP, APIs, MailHog, webhooks; FastMCP 3.1 tools, prompts, sampling.
---

# Email-MCP skill

## When to use

- Sending mail via SMTP or transactional APIs (SendGrid, Mailgun, Resend).
- Reading inbox via IMAP or checking configured services.
- Slack/Discord-style webhook alerts to team channels.

## Tool flow

1. `list_services()` - see what is configured.
2. `email_status()` - verify connectivity before bulk sends.
3. `send_email` / `check_inbox` - core operations.
4. `suggest_email_subject` / `email_agentic_assist` - use when the host supports sampling (or Anthropic fallback if set).

## Prompts

- `email_compose_request` - structured ask to draft an email.
- `email_help_request` - narrow help on one topic.

## Web dashboard

- API on the backend port (see repo `webapp/start.ps1`): `/api/status`, `/api/tools`, `/api/chat`, `/api/skills` (HTTP Basic: `MCP_WEB_USER` / `MCP_WEB_PASSWORD`).
