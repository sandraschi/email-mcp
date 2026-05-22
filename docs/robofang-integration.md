# Integrating email-mcp with robofang

The email-mcp **Mail Watcher** can fire webhook notifications to robofang when new emails arrive. robofang can then trigger TTS alerts, desk light flashes, hands gestures, or dashboard notifications.

## Prerequisites

- robofang running (typically on port 10956)
- email-mcp running (port 10813)
- At least one email service configured with IMAP access

## Quick Setup

### 1. Find robofang's alert endpoint

robofang-mcp exposes an alert endpoint at:

```
http://localhost:10956/api/alerts
```

### 2. Start the Mail Watcher

Via the web dashboard at `/lab`:

1. Go to **Mail Lab** → **Mail Watcher**
2. Enter webhook URL: `http://localhost:10956/api/alerts`
3. Set interval (e.g. 60 seconds)
4. Click **Start Watch**

Via API:

```powershell
curl -X POST http://localhost:10813/api/watcher/start `
  -H "Authorization: Basic sandra:vienna2026" `
  -H "Content-Type: application/json" `
  -d '{"interval":60,"webhook_url":"http://localhost:10956/api/alerts"}'
```

### 3. Test

Send yourself an email or use the Mail Lab's AI Message Generator to inject a test email. The watcher will detect it within the poll interval and POST to robofang.

## Webhook Payload (what robofang receives)

```json
{
  "event": "new_email",
  "service": "default",
  "folder": "INBOX",
  "count": 1,
  "emails": [
    {
      "id": "42",
      "subject": "Budget approval needed",
      "from": "CFO <cfo@company.com>"
    }
  ],
  "timestamp": 1747234567.89
}
```

## What robofang Can Do

| Capability | Description |
|-----------|-------------|
| **TTS Alert** | Speak "New email from CFO: Budget approval needed" |
| **Desk Lights** | Flash red for urgent senders, green for personal |
| **Hands Gesture** | Wave animation on notification |
| **Dashboard** | Show unread count on robofang hub |
| **Logging** | Record all email events to the audit trail |

## Configuration File

Create `email-mcp-to-robofang.json` in robofang's `configs/` directory:

```json
{
  "source": "email-mcp",
  "webhook_url": "http://localhost:10956/api/alerts",
  "filters": {
    "min_priority": "normal",
    "include_folders": ["INBOX"]
  },
  "actions": {
    "tts": true,
    "lights": true,
    "dashboard": true
  }
}
```

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Watcher starts but no webhooks fire | No new emails since watcher started | Send a test email |
| Webhook returns 404 | robofang endpoint wrong | Check robofang port in fleet-registry |
| "Webhook POST failed" in logs | robofang not running | Start robofang, check port |
