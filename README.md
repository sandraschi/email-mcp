# Email MCP

Multi-Service Email Platform for MCP

A comprehensive email MCP server supporting multiple email services including standard SMTP/IMAP providers, transactional email APIs, local testing services, and webhook integrations.

**Version 0.2.1** - AI Email Management Orchestrator Added

See [CHANGELOG.md](CHANGELOG.md) for version history.

## AI Email Management Orchestrator

Combines `email-mcp` + `local-llm-mcp` for AI-assisted email processing:

- **`weed_trash`** - AI-powered email cleanup with intelligent filtering
- **`email_summarizer`** - Smart inbox summaries grouped by topic/sender
- **`smart_email_filter`** - AI-generated filtering rules and organization

Configure email credentials and run: `python email-llm-orchestrator.py`

## Features

### Core Email Functionality
- Multiple Email Services: SMTP/IMAP, SendGrid, Mailgun, Resend, Amazon SES, Postmark
- Local Testing: MailHog, Mailpit, MailCatcher, Inbucket
- Webhook Integrations: Slack, Discord, Telegram, GitHub
- Dynamic Configuration: Add services at runtime without restart
- Backward Compatible: Works with existing SMTP/IMAP configurations
- Async Operations: Non-blocking email operations

### AI Email Management (Orchestrator)
- **`weed_trash`** - AI-powered intelligent email cleanup
- **`email_summarizer`** - Smart inbox summaries by topic and sender
- **`smart_email_filter`** - AI-generated filtering rules
- **Server Compositing** - Combines email-mcp + local-llm-mcp
- **Intelligent Analysis** - LLM understands email content and context

### Standards & Quality
- MCPB Packaging: Complete packaging for Claude Desktop
- CI/CD Pipeline: Automated testing and deployment
- Health Monitoring: Service availability and performance tracking
- Comprehensive Testing: Unit, integration, and service-specific tests

## Standards Compliance

This email-mcp implements current MCP server standards:

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
- Security scanning with Bandit
- Package building and MCPB creation
- **PyPI publishing disabled** (requires PyPI account setup)

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
- **Gmail** - SMTP/IMAP with App Passwords
- **Outlook/Hotmail** - SMTP/IMAP
- **Yahoo Mail** - SMTP/IMAP
- **iCloud Mail** - SMTP/IMAP
- **ProtonMail** - SMTP/IMAP

### Transactional Email APIs
- **SendGrid** - Enterprise email delivery
- **Mailgun** - Developer-friendly email API
- **Resend** - Modern email API
- **Amazon SES** - AWS email service
- **Postmark** - Reliable transactional email

### Local Testing Services
- **MailHog** - Web UI for email testing
- **Mailpit** - Modern mail testing
- **MailCatcher** - Ruby-based testing
- **Inbucket** - Lightweight testing

### Webhook/Dev Services
- **Slack** - Send emails as Slack messages
- **Discord** - Send emails as Discord messages
- **Telegram** - Bot message forwarding
- **GitHub** - Email to issue/PR comments

## Installation

### Standard Installation
```bash
cd email-mcp
pip install -e ".[dev]"
```

### Claude Desktop (MCPB)
1. Download the `email-mcp.mcpb` package (when built)
2. Drag and drop into Claude Desktop settings
3. The server will be automatically configured

### Glama Client
The server is automatically discoverable by Glama.ai's GitHub scraping system through the `glama.json` configuration.

## AI Email Management Orchestrator

**Revolutionary AI-powered email tools** - Combine this server with `local-llm-mcp` for intelligent email processing.

### Quick Setup
```bash
# Install dependencies
pip install fastmcp

# Configure email (see Gmail section below)
export SMTP_USER=your-email@gmail.com
export SMTP_PASSWORD=your-app-password

# Configure LLM (Ollama recommended)
ollama serve  # Start Ollama server
ollama pull llama3  # Download model

# Run orchestrator
python email-llm-orchestrator.py
```

### AI Tools Available
- **`weed_trash`** - Intelligent email cleanup with AI analysis
- **`email_summarizer`** - Smart inbox summaries by topic/sender
- **`smart_email_filter`** - AI-generated filtering rules

For orchestrator usage, see the tools section above.

## Gmail Integration

The email-mcp supports Gmail SMTP with App Password authentication:

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

## ⚙️ Configuration

### Basic SMTP/IMAP (Backward Compatible)

Set environment variables for standard email providers:

```bash
export SMTP_SERVER="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USER="your-email@gmail.com"
export SMTP_PASSWORD="your-app-password"
export IMAP_SERVER="imap.gmail.com"
export IMAP_USER="your-email@gmail.com"
export IMAP_PASSWORD="your-app-password"
```

### API Services

Configure transactional email APIs:

```bash
# SendGrid
export SENDGRID_API_KEY="your-sendgrid-api-key"
export SENDGRID_FROM_EMAIL="noreply@yourdomain.com"

# Mailgun
export MAILGUN_API_KEY="your-mailgun-api-key"
export MAILGUN_DOMAIN="yourdomain.com"
export MAILGUN_FROM_EMAIL="noreply@yourdomain.com"

# Resend
export RESEND_API_KEY="your-resend-api-key"
export RESEND_FROM_EMAIL="noreply@yourdomain.com"
```

### Local Testing Services

Enable local email testing:

```bash
# MailHog
export MAILHOG_ENABLED="true"
export MAILHOG_SMTP_HOST="localhost"
export MAILHOG_SMTP_PORT="1025"
export MAILHOG_HTTP_URL="http://localhost:8025"
```

### Webhook Services

Configure chat/webhook integrations:

```bash
# Slack
export SLACK_WEBHOOK_URL="https://example.com/docs/slack-incoming-webhook"
```

### Cursor IDE Configuration

Add to your `mcp.json`:

```json
{
  "mcpServers": {
    "email-mcp": {
      "command": "python",
      "args": ["-m", "email_mcp.server"],
      "env": {
        "PYTHONPATH": "D:/Dev/repos/email-mcp/src"
      }
    }
  }
}
```

## 📨 Usage Examples

### Send Emails

```python
# Basic SMTP email
send_email(
    to="user@example.com",
    subject="Hello World",
    body="This is a test email"
)

# HTML email with SendGrid
send_email(
    to="user@example.com",
    subject="Welcome",
    body="Welcome to our service!",
    html="<h1>Welcome!</h1><p>Thanks for joining.</p>",
    service="sendgrid"
)

# Email to Slack webhook
send_email(
    to="#general",
    subject="Alert",
    body="System alert message",
    service="slack"
)
```

### Check Inbox

```python
# Check default IMAP inbox
result = check_inbox(limit=10, unread_only=True)
print(f"Found {result['count']} unread emails")

# Check local testing inbox
result = check_inbox(service="mailhog", limit=20)
print(f"Test emails: {result['count']}")
```

### Service Management

```python
# List available services
services = list_services()
print(f"Available services: {list(services['services'].keys())}")

# Configure new service at runtime
configure_service(
    name="my-sendgrid",
    type="api",
    config={
        "api_key": "your-key",
        "api_url": "https://api.sendgrid.com/v3/mail/send",
        "from_email": "noreply@domain.com",
        "service_type": "sendgrid"
    }
)

# Test service connectivity
status = email_status(service="sendgrid")
print(f"SendGrid connected: {status['services']['sendgrid']['connected']}")
```

```

## 🛠️ API Reference

### Tools

| Tool | Description | Services Supported |
|------|-------------|-------------------|
| `send_email` | Send emails via any service | All services |
| `check_inbox` | Check inbox via IMAP/API | SMTP, Local services |
| `email_status` | Test service connectivity | All services |
| `configure_service` | Add services dynamically | Runtime configuration |
| `list_services` | List configured services | Service management |
| `email_help` | Get help and documentation | Documentation |

### Service Types

| Type | Description | Examples | Inbox Support |
|------|-------------|----------|----------------|
| `smtp` | Standard SMTP/IMAP | Gmail, Outlook, Yahoo | ✅ |
| `api` | Transactional APIs | SendGrid, Mailgun, Resend | ❌ |
| `local` | Testing services | MailHog, Mailpit | ✅ |
| `webhook` | Chat integrations | Slack, Discord | ❌ |

## 🎯 Architecture

- **Multi-Service Support** - SMTP, API, Local, Webhook services
- **Dynamic Configuration** - Add services without restart
- **Backward Compatible** - Works with existing SMTP/IMAP configs
- **Async Operations** - Non-blocking email operations
- **Extensible Design** - Easy to add new service types

## ✅ Benefits

- **Comprehensive Coverage** - Supports all major email services
- **Developer Friendly** - Local testing and webhook integrations
- **Flexible Configuration** - Environment variables + runtime config
- **Performance Optimized** - Async operations, connection pooling
- **Easy Integration** - Simple MCP protocol interface  

## Development

```powershell
# Install
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/
ruff check src/
```

### PyPI Publishing Setup (Optional)

When ready to publish to PyPI:

1. **Create PyPI account**: Visit https://pypi.org/account/register/
2. **Generate API token**: Go to https://pypi.org/manage/account/token/
3. **Add to GitHub**: Add `PYPI_API_TOKEN` secret to repository settings
4. **Enable publishing**: Change CI/CD condition from `false` to proper tag condition
5. **Tag release**: `git tag v0.2.1 && git push origin v0.2.1`

## License

MIT

