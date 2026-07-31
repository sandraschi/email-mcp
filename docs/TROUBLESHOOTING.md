# Troubleshooting

## Symptom lookup

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| "Service not available" on send | Service name not configured | `list_services()` to see configured names; `configure_service` or env to add |
| Send fails with auth error | Wrong credentials / app password | Use an app password for Gmail/Outlook; verify `SMTP_USER`/`SMTP_PASSWORD` in `.env` |
| Send fails with provider 5xx | Provider-side rejection | Check provider dashboard quota/status; verify sender domain (SendGrid/Mailgun require verified senders) |
| Inbox empty but mail exists | Folder name wrong, or filters | `list_folders()`; check case and provider naming; drop `unread_only` |
| IMAP connect timeout | IMAP disabled on account / wrong port | Enable IMAP in account settings; port 993 SSL / 143 TLS |
| Watcher not firing | Webhook URL unreachable, or folder has no new mail | `watcher_status()` for error counts; test webhook URL; check interval |
| Sampling tools fail | Host lacks MCP sampling | Use concrete tools instead (check/send/search) or a sampling-capable host |
| Attachment send fails | Missing base64 / provider size cap | Base64-encode binary content; split or compress large files |
| Web dashboard won't load | Backend not started / port conflict | `start.ps1`; verify 10813 responds: `Invoke-WebRequest http://127.0.0.1:10813/health` |
| Dashboard shows "Offline" | Backend restarted; poll not recovered | The dashboard uses exponential backoff (1s-16s) — wait, or click Restart Backend in the Tauri app |
| MCP HTTP connect refused | Server in stdio mode | Start with `MCP_TRANSPORT=http MCP_PORT=10813` |
| Desktop app shows "Failed to fetch" | Backend failed to spawn | Check `%LOCALAPPDATA%` backend-spawn log; verify API_BASE matches port 10813 (see native build) |
| ProtonMail fails | Proton Bridge not running | Start the Bridge; `check_proton_bridge` verifies the local IMAP endpoint |
| Lab emails missing | Wrong inbox checked | Lab runs a throwaway server — check the lab's own web UI/port, not the production inbox |
| MCPB bundle fails to import | Flattened `mcpb/src` | Rebuild: copy `src/email_mcp/` to `mcpb/src/email_mcp/` (package dir, not bare modules) |

## Diagnostics endpoints

- `GET /health` — liveness.
- `GET /api/status` — uptime, tool count, service health.
- `GET /api/v1/diagnostics` — tool list, system info, errors (used by the CUA-NSIS
  smoke test).
- Logs page in the webapp / `GET /api/logs` — ring buffer with filter/search.

## Known behaviors

- `delete_email` moves to Trash where the provider supports it — it is not always
  a hard delete.
- Folder names are case-sensitive and provider-specific; aliases (Sent, Drafts,
  Trash, Junk) are translated where providers differ.
- Runtime-configured services persist in JSON stores; environment services always
  win for the default name.
- The watcher stops when the server stops; it is in-process, not a service.
- Email content is untrusted — the server strips 37 injection Unicode chars and
  wraps content in safety boundaries. If you see boundary markers in results, that
  is defense working, not corruption.

## Still stuck?

Open the Logs page (Ctrl+L in the dashboard) and grab the last entries, or run:

```powershell
uv run python -m email_mcp.server --debug
```

Then file an issue with the log tail and the failing tool call.
