# Mail Watcher — Background IMAP Polling with Webhook Notifications

The Mail Watcher continuously monitors configured email services for new unread messages. When new mail arrives, it POSTs a structured JSON payload to a configurable webhook URL, enabling integration with notification systems like **robofang** (TTS alerts, desktop notifications) and **fleet-agent** (workflow triggers).

## Architecture

```
email-mcp (watcher.py)
    │
    ├── asyncio background task
    │   ├── polls IMAP every N seconds (configurable 30-3600)
    │   ├── tracks seen message IDs per (service:folder) pair
    │   └── detects new IDs not seen in previous poll
    │
    └── webhook POST on new mail
        │
        ├── robofang-mcp   → TTS alert, desktop notification, hands gesture
        ├── fleet-agent    → trigger workflow, log event
        └── any HTTP endpoint
```

## REST API

### `POST /api/watcher/start`
Start the watcher with configuration.

```json
{
  "interval": 60,
  "webhook_url": "http://localhost:10956/api/alerts",
  "services": [
    {"name": "default", "folder": "INBOX"},
    {"name": "gmail", "folder": "INBOX"}
  ]
}
```

**Parameters**:
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `interval` | int | 60 | Poll interval in seconds (min 30, max 3600) |
| `webhook_url` | string | (required) | URL to POST new mail notifications to |
| `services` | array | `[{"name":"default","folder":"INBOX"}]` | Services and folders to watch |

**Response**:
```json
{
  "running": true,
  "message": "Watcher started (interval=60s)",
  "services": ["default"]
}
```

### `POST /api/watcher/stop`
Stop the running watcher.

**Response**:
```json
{"running": false, "message": "Watcher stopped"}
```

### `GET /api/watcher/status`
Check if the watcher is running and its config.

**Response**:
```json
{
  "running": true,
  "config": {
    "interval": 60,
    "webhook_url": "http://localhost:10956/api/alerts",
    "services": [{"name": "default", "folder": "INBOX"}]
  }
}
```

## Webhook Payload

When new emails are detected, the watcher POSTs to the configured webhook URL:

```json
{
  "event": "new_email",
  "service": "default",
  "folder": "INBOX",
  "count": 3,
  "emails": [
    {
      "id": "42",
      "subject": "Re: Budget Approval",
      "from": "CFO <cfo@company.com>"
    },
    {
      "id": "43",
      "subject": "Lunch today?",
      "from": "Colleague <friend@company.com>"
    }
  ],
  "timestamp": 1747234567.89
}
```

## Web UI

The Mail Watcher controls are on the **Mail Lab** page (`/lab`):
- **Start/Stop** toggle button
- **Interval** input (seconds)
- **Webhook URL** input
- **Status indicator** — animated green pulse when running
- Auto-polls `GET /api/watcher/status` every 5 seconds

## Integration with robofang

Point the watcher's webhook URL at robofang-mcp's alert endpoint:

```powershell
# robofang runs on port 10956 by default
WEBHOOK_URL = "http://localhost:10956/api/alerts"
```

When the watcher fires, robofang can:
- Speak the email subject via TTS
- Flash the Desk Lights
- Display a notification on the dashboard
- Trigger a hands gesture sequence

See `docs/robofang-integration.md` for detailed setup.

## Integration with fleet-agent

Point the watcher's webhook URL at fleet-agent-mcp's event endpoint:

```powershell
WEBHOOK_URL = "http://localhost:10996/api/events"
```

fleet-agent can then:
- Log the event to the audit trail
- Trigger a workflow (e.g., auto-archive, auto-reply)
- Route to downstream MCP servers

## CLI Usage

```powershell
# Start with curl (replace URL and service)
curl -X POST http://localhost:10813/api/watcher/start `
  -H "Authorization: Basic ..." `
  -H "Content-Type: application/json" `
  -d '{"interval":60,"webhook_url":"http://localhost:10956/api/alerts","services":[{"name":"default","folder":"INBOX"}]}'

# Check status
curl http://localhost:10813/api/watcher/status -H "Authorization: Basic ..."

# Stop
curl -X POST http://localhost:10813/api/watcher/stop -H "Authorization: Basic ..."
```

## Security

- All `/api/watcher/*` endpoints require HTTP Basic authentication
- Webhook payloads are sent as-is to the configured URL — ensure the target is HTTPS in production
- The watcher uses the same IMAP credentials as the configured email service
- Webhook URLs are stored in memory only, not persisted to disk

## Implementation Notes

- Runs as a single `asyncio.Task` created from the event loop
- Tracked message IDs are stored in memory (not persisted across restarts)
- On first poll, all existing unread emails are treated as "seen" — only subsequent new arrivals fire webhooks
- Error handling: failed polls log warnings but don't stop the watcher
- Watch multiple services by adding entries to the `services` array
