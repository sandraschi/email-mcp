# Fleet Connectors — aiwatcher & robofang

email-mcp can push events into the fleet pipeline the same way arxiv-mcp and
vla-mcp do. Two connectors, both **opt-in** and **fail-soft** (a failure is
logged and returned, never crashes the server):

| Connector | Target | Contract | Env |
|-----------|--------|----------|-----|
| **aiwatcher** | `POST {url}/api/fleet/ingest` | `{title, summary, source, url, urgency_hint}` + `X-AIWatcher-Key` when configured | `EMAIL_MCP_AIWATCHER_URL`, `EMAIL_MCP_AIWATCHER_KEY` |
| **robofang** | `POST {url}/api/hooks/email` | `{from_addr, subject, body}` → robofang inbox processing | `EMAIL_MCP_ROBOFANG_URL` |

## Configuration

```bash
# .env — set a URL to enable that connector
EMAIL_MCP_AIWATCHER_URL=http://127.0.0.1:10946
# EMAIL_MCP_AIWATCHER_KEY=          # required only if AIWATCHER_API_KEY is set on aiwatcher
EMAIL_MCP_ROBOFANG_URL=http://127.0.0.1:10871
```

Note: the robofang bridge binds to the secure address (Tailscale IP when
Tailscale is running), not 127.0.0.1 — set `EMAIL_MCP_ROBOFANG_URL` to the
actual bind address (check `Get-NetTCPConnection -LocalPort 10871`).

## Usage

MCP tool:

```
email_connector(operation="aiwatcher", title="Urgent: payment due",
                summary="Invoice overdue", url="...", urgency_hint=8.0)
email_connector(operation="robofang", from_addr="sender@x.com",
                subject="Alert", body="Backup failed")
email_connector(operation="status")
```

REST (same auth as the dashboard):

| Endpoint | Purpose |
|----------|---------|
| `GET  /api/connectors/status` | Probe both connectors (enabled + online) |
| `POST /api/connectors/aiwatcher` | `{title, summary, url, urgency_hint}` |
| `POST /api/connectors/robofang` | `{from_addr, subject, body}` |

## aiwatcher

Ingests events into aiwatcher's news pipeline (linked to interest bundles with
the "Fleet Events" pattern). When `AIWATCHER_API_KEY` is set on aiwatcher,
producers must send it via `EMAIL_MCP_AIWATCHER_KEY`.

## robofang

Sends an email-shaped message into robofang's inbox hook — robofang processes
it (`process_inbox_message`) and may reply to the sender. Robofang also accepts
fleet alert events at `POST /api/v1/events` (`{source, event, urgency, title,
url, summary, tags, timestamp}`), which stores them in the audit log and
broadcasts when `urgency >= 8.0` — see the robofang repo.
