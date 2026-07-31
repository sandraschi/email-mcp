# Tools

Email MCP registers 39 MCP tools. Every tool returns a dict with `success` and a
natural-language `message`; failures include `error` with recovery guidance.
Email content in results is safety-wrapped against prompt injection.

## Sending

| Tool | Description |
|------|-------------|
| `send_email(to, subject, body, service, html, cc, bcc, attachments)` | Send via any configured service (SMTP/API/local/webhook). `to` accepts string, comma-separated, or list. |

## Receiving

| Tool | Description |
|------|-------------|
| `check_inbox(service, folder, limit, unread_only, from_contains, subject_contains)` | List emails with server-side filters. |
| `fetch_email_detail(email_id, service, folder)` | Full message: text + HTML body, headers. |
| `search_emails(query, service, folder, limit)` | IMAP SEARCH across subject/from/body. |
| `move_email(email_id, to_folder, service, folder)` | Move between IMAP folders. |
| `flag_spam(email_id, service, folder)` | Junk flag + move to Spam. |
| `delete_email(email_id, service, folder)` | Delete (Trash move where supported). |
| `mark_email_read(email_id, service, folder)` / `mark_email_unread(...)` | Toggle SEEN flag. |

## Folders

| Tool | Description |
|------|-------------|
| `list_folders(service)` | List mailboxes. |
| `create_folder(name, service)` | Create folder. |
| `delete_folder(name, service)` | Delete folder. |
| `rename_folder(old_name, new_name, service)` | Rename folder. |

## Services

| Tool | Description |
|------|-------------|
| `list_services()` | Configured services + capabilities. |
| `configure_service(name, type, config, enabled)` | Add a service at runtime (smtp/api/local/webhook). |
| `remove_service(name)` | Remove a runtime service. |
| `email_status(service)` | Connectivity probe per service. |

Quick setup presets (Gmail, Outlook, Yahoo, iCloud, ProtonMail, Zoho, GMX,
Fastmail) and `check_proton_bridge` are exposed via REST (`/api/services/quick`).

## Mailing Lists

| Tool | Description |
|------|-------------|
| `mailing_lists_catalog()` | List presets from `EMAIL_MCP_MAILING_LISTS`. |
| `mailing_list_latest(list_id, limit, unread_only)` | Newest drop for a preset. |

## Contacts

| Tool | Description |
|------|-------------|
| `add_contact(name, email, phone, notes, group)` | Create contact. |
| `search_contacts(query)` | Match by name or email. |

CSV/vCard/Google/Microsoft imports, curated official lists, and groups are in the
webapp (Contacts page).

## Auto-Respond

| Tool | Description |
|------|-------------|
| `add_auto_rule(...)` | Register a rule (trigger, action, tone, template). |
| `list_auto_rules()` | List rules. |
| `delete_auto_rule(rule_id)` | Delete a rule. |
| `list_pending_replies()` | AI drafts awaiting approval. |
| `approve_reply(pending_id)` | Approve and queue a reply. |
| `auto_respond_now(email_id)` | Trigger the rule engine on one message. |

## Watcher

| Tool | Description |
|------|-------------|
| `start_watcher(interval, webhook_url, services)` | Background IMAP polling with webhook POSTs. |
| `stop_watcher()` | Stop polling. |
| `watcher_status()` | Running state, errors, last poll. |

## Creative Workflows

| Tool | Description |
|------|-------------|
| `run_workflow(workflow, recipient, tone, mood, format)` | Preset creative emails (love-letter, breakup, thank-you, complaint, apology, fan-mail, hate-mail; formats text/ascii/svg). |

## AI Assistance

| Tool | Description |
|------|-------------|
| `suggest_email_subject(context)` | 1-3 subject lines (needs host sampling). |
| `email_agentic_assist(goal)` | Multi-step email workflow plan (needs host sampling). |

## Cards (Prefab)

| Tool | Description |
|------|-------------|
| `show_email_status_card()` | Status as rich card. |
| `show_inbox_card(limit)` | Inbox as rich card. |
| `show_services_card()` | Services as rich card. |
| `show_mailing_list_digest_card()` | Digest as rich card. |

## Support

| Tool | Description |
|------|-------------|
| `email_help(topic)` | In-chat documentation. |
| `email_shutdown(confirm)` | Graceful shutdown (requires `confirm=True`). |

## REST surface (port 10813)

`GET /health`, `GET /api/status`, `GET /api/v1/diagnostics`,
`GET /api/capabilities`, `GET /api/skills`, `GET /api/skills/{name}`,
`GET /api/llm/models`, `GET /api/llm/discover`, `POST /api/llm/configure`,
`POST /api/chat`, `POST /api/send`, `POST /api/improve`, `POST /api/workflow`,
`GET /api/services`, `POST /api/services/quick`. OpenAPI docs at `/docs`.
