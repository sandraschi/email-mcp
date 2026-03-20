# Cursor Setup for Multi-Service Email MCP

## 🚀 **New Multi-Service Capabilities**

The minimail-mcp now supports **15+ email services** including:
- **SMTP/IMAP**: Gmail, Outlook, Yahoo, iCloud, ProtonMail
- **Transactional APIs**: SendGrid, Mailgun, Resend, Amazon SES
- **Local Testing**: MailHog, Mailpit, MailCatcher, Inbucket
- **Webhooks**: Slack, Discord, Telegram, GitHub

## ⚙️ **Configuration Options**

### Basic Setup (Project-level)

**Config location**: `D:\Dev\repos\.cursor\mcp.json`

```json
{
  "mcpServers": {
    "minimail-mcp": {
      "command": "python",
      "args": ["-m", "email_mcp.server"],
      "env": {
        "PYTHONPATH": "D:/Dev/repos/email-mcp/src"
      }
    }
  }
}
```

### Environment Variables (Multiple Options)

Add environment variables to the `env` section above:

#### **SMTP/IMAP (Standard Email)**
```json
"env": {
  "SMTP_SERVER": "smtp.gmail.com",
  "SMTP_PORT": "587",
  "SMTP_USER": "your-email@gmail.com",
  "SMTP_PASSWORD": "your-app-password",
  "SMTP_FROM": "your-email@gmail.com",
  "IMAP_SERVER": "imap.gmail.com",
  "IMAP_PORT": "993",
  "IMAP_USER": "your-email@gmail.com",
  "IMAP_PASSWORD": "your-app-password"
}
```

#### **SendGrid API**
```json
"env": {
  "SENDGRID_API_KEY": "your-sendgrid-api-key",
  "SENDGRID_FROM_EMAIL": "noreply@yourdomain.com"
}
```

#### **Mailgun API**
```json
"env": {
  "MAILGUN_API_KEY": "your-mailgun-api-key",
  "MAILGUN_DOMAIN": "yourdomain.com",
  "MAILGUN_FROM_EMAIL": "noreply@yourdomain.com"
}
```

#### **Resend API**
```json
"env": {
  "RESEND_API_KEY": "your-resend-api-key",
  "RESEND_FROM_EMAIL": "noreply@yourdomain.com"
}
```

#### **Local Testing (MailHog)**
```json
"env": {
  "MAILHOG_ENABLED": "true",
  "MAILHOG_SMTP_HOST": "localhost",
  "MAILHOG_SMTP_PORT": "1025",
  "MAILHOG_HTTP_URL": "http://localhost:8025"
}
```

#### **Slack Webhook**
```json
"env": {
  "SLACK_WEBHOOK_URL": "https://example.com/docs/slack-incoming-webhook"
}
```

## 🧪 **Testing the Setup**

### 1. Restart Cursor MCP
- Command Palette (`Ctrl+Shift+P`)
- Type "Reload MCP Servers" or "Developer: Reload Window"

### 2. Check Available Services
```python
# In Composer (Ctrl+L)
list_services()
```

### 3. Test Email Sending

#### SMTP/IMAP Test
```python
send_email(
    to="test@example.com",
    subject="Test Email",
    body="Hello from multi-service email MCP!"
)
```

#### SendGrid Test
```python
send_email(
    to="user@example.com",
    subject="Welcome",
    body="Welcome email via SendGrid!",
    service="sendgrid"
)
```

#### Slack Test
```python
send_email(
    to="#general",
    subject="Alert",
    body="Test message via Slack webhook",
    service="slack"
)
```

#### Local Testing
```python
send_email(
    to="test@localhost",
    subject="Test",
    body="Check MailHog web UI",
    service="mailhog"
)
```

### 4. Test Inbox Checking
```python
# Check default IMAP inbox
check_inbox(limit=5)

# Check local testing inbox
check_inbox(service="mailhog", limit=10)
```

### 5. Test Service Status
```python
# Check all services
email_status()

# Check specific service
email_status(service="sendgrid")
```

## Gmail App Password Setup

If using Gmail, you need an App Password (not your regular password):

1. Go to [Google Account Settings](https://myaccount.google.com/)
2. Security → 2-Step Verification (must be enabled)
3. App Passwords → Generate new app password
4. Use that password in the config

## Notes

- The config is at project level (`.cursor/mcp.json`)
- Cursor will merge this with user-level configs
- Environment variables are set per-server in the `env` section
- Credentials are stored in the config file (keep it secure!)

