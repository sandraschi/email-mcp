# Email MCP Server - User Interaction Guide

## How to Use the Email MCP Server

### Basic Email Sending

**Send a simple email:**
```
send_email(
    to="user@example.com",
    subject="Hello World",
    body="This is a test email"
)
```

**Send HTML email:**
```
send_email(
    to="user@example.com",
    subject="Welcome",
    body="Please view in HTML mode",
    html="<h1>Welcome!</h1><p>Thank you for joining.</p>"
)
```

**Send with CC/BCC:**
```
send_email(
    to="primary@example.com",
    cc=["manager@example.com"],
    bcc=["admin@example.com"],
    subject="Team Update",
    body="Important team information"
)
```

### Service Selection

**Use specific email service:**
```
send_email(
    to="user@example.com",
    subject="Test",
    body="Message",
    service="sendgrid"
)
```

Available services: smtp, sendgrid, mailgun, resend, slack, discord

### Inbox Management

**Check inbox:**
```
result = check_inbox(limit=10, unread_only=True)
print(f"Found {result['count']} unread emails")
```

**Check specific folder:**
```
result = check_inbox(folder="Sent", limit=5)
```

**Filter by date:**
```
from datetime import datetime, timedelta
week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
result = check_inbox(after_date=week_ago)
```

### Service Management

**List available services:**
```
services = list_services()
for service in services['services']:
    print(f"{service}: {services['services'][service]['type']}")
```

**Check service status:**
```
status = email_status()
for service_name, service_info in status['services'].items():
    print(f"{service_name}: {service_info['connected']}")
```

**Configure new service:**
```
configure_service(
    name="my-gmail",
    type="smtp",
    config={
        "server": "smtp.gmail.com",
        "port": 587,
        "username": "user@gmail.com",
        "password": "app-password"
    }
)
```

### Configuration Examples

**Gmail SMTP Setup:**
```
# Environment variables
export SMTP_SERVER="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USER="your-email@gmail.com"
export SMTP_PASSWORD="your-app-password"
```

**SendGrid API Setup:**
```
export SENDGRID_API_KEY="your-sendgrid-api-key"
export SENDGRID_FROM_EMAIL="noreply@yourdomain.com"
```

**MailHog for Testing:**
```
export MAILHOG_ENABLED="true"
export MAILHOG_SMTP_HOST="localhost"
export MAILHOG_SMTP_PORT="1025"
```

### Error Handling

**Common issues and solutions:**

1. **Authentication failed:**
   - For Gmail/Outlook: Use App Password, not regular password
   - Enable 2FA on your account
   - Check SMTP server settings

2. **Connection timeout:**
   - Verify SMTP server and port
   - Check firewall settings
   - Try different service (sendgrid instead of smtp)

3. **Service not configured:**
   - Run configure_service() to add the service
   - Check environment variables
   - Verify API keys

### Best Practices

1. **Use App Passwords** for Gmail/Outlook instead of regular passwords
2. **Test with local services** (MailHog) during development
3. **Monitor service health** with email_status() regularly
4. **Handle errors gracefully** with try/catch blocks
5. **Use appropriate services** for different use cases:
   - SMTP for standard emails
   - SendGrid/Mailgun for transactional emails
   - Slack/Discord for team notifications

### Advanced Features

**Webhook integrations:**
```
send_email(
    to="#general",
    subject="Alert",
    body="System notification",
    service="slack"
)
```

**Multiple recipients:**
```
send_email(
    to=["user1@example.com", "user2@example.com"],
    subject="Group Message",
    body="Message for multiple recipients"
)
```

**Date filtering:**
```
# Emails from last week
result = check_inbox(
    after_date="2024-01-01",
    before_date="2024-01-15"
)
```

This server provides comprehensive email capabilities for all your communication needs.