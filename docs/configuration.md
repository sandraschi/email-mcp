# Configuration Reference

## Environment Variables

### Core SMTP/IMAP (backward compatible)
| Variable | Description |
|----------|-------------|
| `SMTP_SERVER` | SMTP server hostname |
| `SMTP_PORT` | SMTP port (default: 587) |
| `SMTP_USER` | SMTP username |
| `SMTP_PASSWORD` | SMTP password |
| `SMTP_FROM` | From address (defaults to SMTP_USER) |
| `IMAP_SERVER` | IMAP server hostname |
| `IMAP_PORT` | IMAP port (default: 993) |
| `IMAP_USER` | IMAP username (defaults to SMTP_USER) |
| `IMAP_PASSWORD` | IMAP password |

### API Services
| Variable | Description |
|----------|-------------|
| `SENDGRID_API_KEY` | SendGrid API key |
| `SENDGRID_FROM_EMAIL` | SendGrid sender address |
| `MAILGUN_API_KEY` | Mailgun API key |
| `MAILGUN_DOMAIN` | Mailgun verified domain |
| `MAILGUN_FROM_EMAIL` | Mailgun sender address |
| `RESEND_API_KEY` | Resend API key |
| `RESEND_FROM_EMAIL` | Resend sender address |

### Local Testing
| Variable | Description |
|----------|-------------|
| `MAILHOG_ENABLED` | Set to "true" to enable MailHog |
| `MAILHOG_SMTP_HOST` | MailHog SMTP host (default: localhost) |
| `MAILHOG_SMTP_PORT` | MailHog SMTP port (default: 1025) |
| `MAILHOG_HTTP_URL` | MailHog web UI URL |

### Webhooks
| Variable | Description |
|----------|-------------|
| `SLACK_WEBHOOK_URL` | Slack incoming webhook URL |
| `DISCORD_WEBHOOK_URL` | Discord webhook URL |

### Mailing Lists
| Variable | Description |
|----------|-------------|
| `EMAIL_MCP_MAILING_LISTS` | JSON array of mailing list presets |
| `EMAIL_MCP_MAILING_LISTS_FILE` | Path to JSON file (same schema) |

### AI Provider
| Variable | Description |
|----------|-------------|
| `AI_PROVIDER` | AI provider (ollama, lmstudio, openai, anthropic, google) |
| `AI_MODEL` | Model name for the AI provider |
| `AI_ENDPOINT` | Custom endpoint URL |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `OPENAI_API_KEY` | OpenAI API key |
| `GOOGLE_API_KEY` | Google AI API key |

### Server
| Variable | Description |
|----------|-------------|
| `MCP_TRANSPORT` | Transport mode (stdio, http, sse) |
| `MCP_HOST` | Bind address (default: 127.0.0.1) |
| `MCP_PORT` | HTTP port (default: 10813) |
| `MCP_PATH` | HTTP endpoint path (default: /mcp) |
| `MCP_WEB_USER` | Web dashboard username |
| `MCP_WEB_PASSWORD` | Web dashboard password |

## Mailing List Presets

Configure named newsletter presets via `EMAIL_MCP_MAILING_LISTS`:

```json
[
  {
    "id": "alphasignal",
    "service": "default",
    "folder": "INBOX",
    "limit": 5,
    "unread_only": true,
    "from_contains": "newsletter@alpha.com",
    "subject_contains": null
  },
  {
    "id": "github-notifications",
    "service": "default",
    "folder": "INBOX",
    "limit": 10,
    "unread_only": false,
    "from_contains": "notifications@github.com",
    "subject_contains": null
  }
]
```

## Dynamic Service Configuration

All services can be added at runtime via the `configure_service` MCP tool or through the webapp's Services page. Configurations are stored in memory and lost on restart unless persisted via environment variables.
