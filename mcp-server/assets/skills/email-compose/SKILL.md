---
description: Compose and send emails using the email MCP server (send_email, check_inbox, list_services)
---

# Email Compose (email-mcp)

**Description:** Compose, send, and manage email via the email MCP server. Covers drafting, templates, threading, attachment handling, send/receive workflow, subject line generation, and multi-service delivery (SMTP, SendGrid, Mailgun, Resend).

## Trigger Phrases

- "Send an email to [recipient] about [subject]"
- "Draft a reply to [message]"
- "Check my inbox for new messages"
- "Forward this email to [person]"
- "Send a follow-up on [thread]"
- "Compose a professional email about [topic]"
- "What email services are configured?"
- "Test my email connection"

## Tools

- **`send_email(to, subject, body, service, html, cc, bcc, attachments)`** — Send email via configured service. Required: `to`, `subject`, `body`. Optional: `service` (default: first configured), `html` (HTML body), `cc`, `bcc`, `attachments` (file paths).
- **`check_inbox(service, folder, limit, unread_only)`** — List messages from IMAP or local test services. Returns sender, subject, date, snippet, read status.
- **`fetch_email_detail(service, message_id)`** — Get full email body and headers for a specific message.
- **`delete_email(service, message_id)`** — Delete a message from the server.
- **`mark_email_read(service, message_id, is_read=True)`** — Mark message as read or unread.
- **`search_emails(service, query, folder, limit)`** — Search emails by subject, sender, or body text.
- **`list_services()`** — List configured email services with their type (SMTP, SendGrid, Mailgun, Resend, MailHog, Slack, Discord).
- **`email_status()`** — Test connectivity for all configured services. Use before bulk sends.
- **`suggest_email_subject(body, tone)`** — LLM-based subject line generation (uses sampling). Provide body text, get 3-5 subject suggestions.

## Prompts

- **`email_compose_request`** — Generates a structured compose request: recipient, purpose, tone, key points.
- **`email_help_request`** — Generates a narrow help request for a specific email topic.

## Workflow

1. **Service check**: `list_services()` to see what's configured. `email_status()` to verify connectivity.
2. **Compose**: Use `suggest_email_subject(body="...")` or write manually. Call `send_email(to=..., subject=..., body=..., service=...)`.
3. **Include attachments**: Pass file paths in `attachments` parameter. Supported: PDF, DOCX, images, ZIP.
4. **Track**: Use `check_inbox()` with `unread_only=True` to monitor replies. Use `search_emails()` to find thread context.
5. **Threading**: For replies, include `In-Reply-To` and `References` headers via `send_email` with `reply_to_message_id`.

## Examples

- "Send a follow-up to the client." → `check_inbox(search="client meeting")` → `send_email(to="client@example.com", subject="Follow-up", body="Thanks for the meeting...", service="gmail")`
- "Check my unread emails." → `check_inbox(unread_only=True, limit=20)`
- "Draft a professional email about project delay." → `suggest_email_subject(body="We need to push the deadline...")` → `send_email(to="team@example.com", subject="Project Timeline Update", body="...", tone="professional")`
