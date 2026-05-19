# Webhook Integrations

## Slack

Send emails as Slack messages to a channel.

### Setup
1. Create a Slack App at https://api.slack.com/apps
2. Enable Incoming Webhooks
3. Create a webhook URL for your channel

### Configuration
```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/T00/B00/xxxxx"
```

### MCP Tool
```
configure_service(name="slack", type="webhook", config={
  "webhook_url": "https://hooks.slack.com/services/T00/B00/xxxxx",
  "service_type": "slack"
})
```

Usage: `send_email(to="#general", subject="Alert", body="CPU at 90%", service="slack")`

## Discord

Send emails as Discord embed messages.

### Setup
1. Go to Server Settings → Integrations → Webhooks
2. Create a webhook and copy the URL

### Configuration
```bash
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/xxxxx/yyyyy"
```

### MCP Tool
```
configure_service(name="discord", type="webhook", config={
  "webhook_url": "https://discord.com/api/webhooks/xxxxx/yyyyy",
  "service_type": "discord"
})
```

## Telegram

Send email notifications via Telegram bot.

### Configuration
```
configure_service(name="telegram", type="webhook", config={
  "webhook_url": "https://api.telegram.org/bot<TOKEN>/sendMessage",
  "service_type": "telegram"
})
```

## Notes
- Webhook services support sending only (no inbox)
- Messages appear as chat messages, not emails
- Services may have rate limits and content restrictions
