# Email MCP Examples

This directory contains practical examples demonstrating how to use the Email MCP multi-service platform.

## 📁 Examples Overview

| Example | Description | Services Covered |
|---------|-------------|------------------|
| `smtp_imap_example.py` | Standard email providers | Gmail, Outlook, Yahoo, iCloud, ProtonMail |
| `api_services_example.py` | Transactional email APIs | SendGrid, Mailgun, Resend, Amazon SES |
| `local_and_webhook_example.py` | Dev/testing integrations | MailHog, Slack, Discord, Telegram |

## 🚀 Running Examples

### Prerequisites

1. **Install the minimail-mcp package:**
   ```bash
   cd minimail-mcp
   pip install -e ".[dev]"
   ```

2. **Configure your services** in environment variables or Cursor config

3. **Start the MCP server** (examples assume MCP server is running)

### Running Individual Examples

```bash
# SMTP/IMAP examples
python examples/smtp_imap_example.py

# API service examples
python examples/api_services_example.py

# Local testing and webhook examples
python examples/local_and_webhook_example.py
```

## 🔧 Example Categories

### 1. SMTP/IMAP Services

**Use cases:**
- Personal email sending/receiving
- Business communications
- Newsletter distribution (small scale)
- Transactional emails (basic)

**Supported providers:**
- Gmail, Outlook/Hotmail, Yahoo Mail
- iCloud Mail, ProtonMail
- Custom SMTP/IMAP servers

### 2. Transactional Email APIs

**Use cases:**
- Welcome emails, password resets
- Order confirmations, receipts
- Marketing newsletters (large scale)
- System notifications

**Supported APIs:**
- SendGrid (high deliverability)
- Mailgun (developer-friendly)
- Resend (modern API)
- Amazon SES (enterprise)
- Postmark (reliable delivery)

### 3. Local Testing Services

**Use cases:**
- Development and testing
- Email template testing
- CI/CD pipeline testing
- QA environments

**Supported tools:**
- MailHog (web UI, SMTP/IMAP)
- Mailpit (modern replacement)
- MailCatcher (Ruby-based)
- Inbucket (lightweight)

### 4. Webhook/Integration Services

**Use cases:**
- Chat notifications
- Alert systems
- Social media posting
- DevOps integrations

**Supported platforms:**
- Slack (team notifications)
- Discord (gaming/community)
- Telegram (bot messaging)
- GitHub (issue/PR updates)

## ⚙️ Configuration Examples

### Gmail Setup
```bash
export SMTP_SERVER="smtp.gmail.com"
export SMTP_USER="your-email@gmail.com"
export SMTP_PASSWORD="your-app-password"
export IMAP_SERVER="imap.gmail.com"
```

### SendGrid Setup
```bash
export SENDGRID_API_KEY="SG.xxxxxxxxxxxxxxxxxxxxxxxxxx"
export SENDGRID_FROM_EMAIL="noreply@yourdomain.com"
```

### MailHog Setup
```bash
export MAILHOG_ENABLED="true"
# MailHog typically runs on localhost:1025 (SMTP) and localhost:8025 (web UI)
```

### Slack Setup
```bash
export SLACK_WEBHOOK_URL="https://example.com/docs/slack-incoming-webhook"
```

## 🔄 MCP Integration

These examples show how the functions would be called through the MCP protocol. In practice:

1. **Cursor IDE** users call these functions directly in Composer
2. **Other MCP clients** use the MCP protocol to invoke tools
3. **Custom integrations** can use the MCP SDK

### Example MCP Calls

```python
# Direct email sending
send_email(
    to="user@example.com",
    subject="Hello",
    body="Message content",
    service="sendgrid"
)

# Inbox checking
check_inbox(service="default", limit=10, unread_only=True)

# Service management
list_services()
email_status()
configure_service(name="my-api", type="api", config={...})
```

## 🧪 Testing the Examples

### With Real Services
```bash
# Set environment variables for your services
export SENDGRID_API_KEY="your-key"
export SLACK_WEBHOOK_URL="your-webhook"

# Run examples
python examples/api_services_example.py
python examples/local_and_webhook_example.py
```

### With Local Testing Only
```bash
# Start MailHog first
docker run -d -p 1025:1025 -p 8025:8025 mailhog/mailhog

# Set local testing variables
export MAILHOG_ENABLED="true"

# Run local examples
python examples/local_and_webhook_example.py
```

## 📚 Additional Resources

- [README.md](../README.md) - Complete documentation
- [CURSOR_SETUP.md](../CURSOR_SETUP.md) - Cursor IDE setup guide
- [tests/README.md](../tests/README.md) - Testing documentation
- [cursor-config-template.json](../cursor-config-template.json) - Configuration templates

## 🤝 Contributing Examples

To add new examples:

1. Create `examples/[category]_example.py`
2. Include comprehensive docstrings
3. Add error handling examples
4. Update this README.md
5. Test with multiple service types

**Example structure:**
```python
#!/usr/bin/env python3
"""
Example Name - Brief Description

Detailed description of what this example demonstrates.
"""

async def main():
    """Main example function."""
    # Implementation here

if __name__ == "__main__":
    # Usage instructions when run directly
    print("Run this through MCP: function_name(args)")
```
