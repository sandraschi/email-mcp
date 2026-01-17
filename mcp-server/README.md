# Email MCP

Multi-Service Email Platform for MCP

A comprehensive email MCP server supporting multiple email services including standard SMTP/IMAP providers, transactional email APIs, local testing services, and webhook integrations.

## Features

- Multiple Email Services: SMTP/IMAP, SendGrid, Mailgun, Resend, Amazon SES, Postmark
- Local Testing: MailHog, Mailpit, MailCatcher, Inbucket
- Webhook Integrations: Slack, Discord, Telegram, GitHub
- Dynamic Configuration: Add services at runtime without restart
- Backward Compatible: Works with existing SMTP/IMAP configurations
- Async Operations: Non-blocking email operations
- MCPB Packaging: Complete packaging for Claude Desktop
- CI/CD Pipeline: Automated testing and deployment
- Health Monitoring: Service availability and performance tracking
- Comprehensive Testing: Unit, integration, and service-specific tests

## Standards Compliance

This minimail-mcp implements current MCP server standards:

### MCPB Packaging (Claude Desktop)
- Complete `manifest.json` with tool definitions
- Prompt templates for Claude Desktop integration
- Self-contained source code packaging
- Icon and documentation assets

### Glama Integration
- `glama.json` configuration for Glama MCP client discovery
- Feature categorization and capability descriptions
- Code review and documentation generation configuration
- Status and development information

### CI/CD Pipeline
- GitHub Actions workflow with multi-Python version testing (3.10, 3.11, 3.12)
- Automated linting with Ruff
- Type checking with MyPy
- Test coverage reporting
- Package building and publishing

### Monitoring Stack
- Health check system for email services
- Performance metrics collection
- System resource monitoring
- Service availability tracking

### Development Standards
- Testing suite with pytest
- Code quality enforcement with Ruff and MyPy
- Project structure with src/ layout
- Dependency management with pyproject.toml
- Documentation and examples

## Supported Services

### Standard Email Providers
- Gmail - SMTP/IMAP with App Passwords
- Outlook/Hotmail - SMTP/IMAP
- Yahoo Mail - SMTP/IMAP
- iCloud Mail - SMTP/IMAP
- ProtonMail - SMTP/IMAP

### Transactional Email APIs
- SendGrid - Enterprise email delivery
- Mailgun - Developer-friendly email API
- Resend - Modern email API
- Amazon SES - AWS email service
- Postmark - Reliable transactional email

### Local Testing Services
- MailHog - Web UI for email testing
- Mailpit - Modern mail testing
- MailCatcher - Ruby-based testing
- Inbucket - Lightweight testing

### Webhook/Dev Services
- Slack - Send emails as Slack messages
- Discord - Send emails as Discord messages
- Telegram - Bot message forwarding
- GitHub - Email to issue/PR comments

## Installation

### Claude Desktop (MCPB)
This package is designed for Claude Desktop. Simply drag and drop the .mcpb file into Claude Desktop settings.

### Manual Installation
```bash
pip install -e ".[dev]"
```

## Gmail Integration

The minimail-mcp supports Gmail SMTP with App Password authentication:

### Configuration
```json
{
  "SenderEmail": "your-email@gmail.com",
  "SenderName": "Your Name",
  "SmtpServer": "smtp.gmail.com",
  "SmtpPort": 587,
  "SmtpUsername": "your-email@gmail.com",
  "SmtpPassword": "your-gmail-app-password"
}
```

### Setup Steps
1. Enable 2-Factor Authentication on Gmail account
2. Generate App Password at https://myaccount.google.com/apppasswords
3. Use App Password for SMTP authentication
4. Configure using `configure_service()` or environment variables

### Supported Features
- SMTP email sending with TLS encryption
- HTML and plain text email formats
- CC/BCC recipient support
- Authentication with App Passwords
- Error handling and connection testing

## Usage Examples

### Send Emails

```python
# Send basic email
send_email(
    to="user@example.com",
    subject="Hello World",
    body="This is a test email"
)

# Send HTML email
send_email(
    to="user@example.com",
    subject="Welcome",
    body="Please view in HTML mode",
    html="<h1>Welcome!</h1><p>Thank you for joining.</p>"
)
```

### Check Inbox

```python
# Check for unread emails
result = check_inbox(limit=10, unread_only=True)
print(f"Found {result['count']} unread emails")
```

### Service Management

```python
# List available services
services = list_services()

# Check service health
status = email_status()

# Configure new service
configure_service(
    name="gmail-smtp",
    type="smtp",
    config={
        "server": "smtp.gmail.com",
        "port": 587,
        "username": "user@gmail.com",
        "password": "app-password"
    }
)
```

## Configuration

### Environment Variables

```bash
# SMTP/IMAP
export SMTP_SERVER="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USER="your-email@gmail.com"
export SMTP_PASSWORD="your-app-password"

# SendGrid
export SENDGRID_API_KEY="your-sendgrid-api-key"

# Slack
export SLACK_WEBHOOK_URL="https://example.com/docs/slack-incoming-webhook"
```

### Runtime Configuration

Services can be configured dynamically at runtime using the `configure_service()` tool.

## Architecture

- **Multi-Service Support**: SMTP, API, Local, Webhook services
- **Dynamic Configuration**: Add services without server restart
- **Backward Compatible**: Works with existing SMTP/IMAP configs
- **Async Operations**: Non-blocking email operations
- **Extensible Design**: Easy to add new service types

## Version 0.2.0 - SOTA Standards Compliant

See [CHANGELOG.md](CHANGELOG.md) for version history.

## License

MIT