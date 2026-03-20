---
description: Compose and send emails using the email MCP server (send_email, check_inbox, list_services)
---

# Email Compose (email-mcp)

Use the email MCP tools to compose, send, and manage email.

## Tools

- **send_email** — Send via SMTP, SendGrid, Mailgun, Resend, MailHog, Slack, Discord. Required: `to`, `subject`, `body`. Optional: `service`, `html`, `cc`, `bcc`.
- **check_inbox** — List messages (IMAP, MailHog, Mailpit). Params: `service`, `folder`, `limit`, `unread_only`.
- **list_services** — List configured services. Call before sending to see available `service` names.
- **email_status** — Test connectivity. Use to verify credentials.
- **suggest_email_subject** — Ask the LLM to suggest subject lines for a body (uses sampling).

## Prompts

- **email_compose_request** — Generates a compose request (recipient, purpose, tone).
- **email_help_request** — Generates a help request for a topic.

## Order

1. Optionally `list_services()` or `email_status()` to see/config services.
2. Use `suggest_email_subject(body="...")` or write subject yourself.
3. `send_email(to=..., subject=..., body=..., service=...)`.
