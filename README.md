# Email MCP Server

Multi-service email platform for MCP-compatible clients.

**Version 0.3.0** - FastMCP 2.14.3 Standards Compliance

See [CHANGELOG.md](CHANGELOG.md) for version history.

## Features

### Email Services
- **SMTP/IMAP**: Standard email providers (Gmail, Outlook, Yahoo, iCloud, ProtonMail)
- **Transactional APIs**: SendGrid, Mailgun, Resend, Amazon SES, Postmark
- **Local Testing**: MailHog, Mailpit, MailCatcher, Inbucket
- **Webhook Integration**: Slack, Discord, Telegram, GitHub

### Core Functionality
- Send emails via multiple service types
- Check inbox via IMAP and service APIs
- Dynamic service configuration at runtime
- Email header decoding (UTF-8, Base64, Quoted-Printable)
- Async operations with connection pooling
- Service health monitoring and testing

### Standards Compliance
- FastMCP 2.14.3 protocol support
- MCPB packaging for Claude Desktop
- Zed extension support
- Conversational tool returns
- Structured logging with JSON output

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
- **ProtonMail** - SMTP/IMAP (requires ProtonMail Bridge for free accounts, or paid account for direct access)

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
cd minimail-mcp
pip install -e ".[dev]"
```

### Claude Desktop (MCPB)
1. Download the `minimail-mcp.mcpb` package (when built)
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

## ProtonMail Integration

The minimail-mcp supports ProtonMail with different setup requirements based on your account type:

### Free Accounts (ProtonMail Bridge Required)

Free ProtonMail accounts require the ProtonMail Bridge application:

#### Setup Steps
1. Download ProtonMail Bridge: https://proton.me/mail/bridge
2. Install and configure Bridge with your ProtonMail account
3. Bridge creates local SMTP/IMAP servers (default ports: 1025 SMTP, 1143 IMAP)

#### Configuration
```json
{
  "SenderEmail": "your@protonmail.com",
  "SenderName": "Your Name",
  "SmtpServer": "127.0.0.1",
  "SmtpPort": 1025,
  "SmtpUsername": "your-username",
  "SmtpPassword": "your-protonmail-password",
  "ImapServer": "127.0.0.1",
  "ImapPort": 1143,
  "ImapUsername": "your-username",
  "ImapPassword": "your-protonmail-password"
}
```

#### Environment Variables
```bash
export SMTP_SERVER="127.0.0.1"
export SMTP_PORT="1025"
export SMTP_USER="your-username"
export SMTP_PASSWORD="your-protonmail-password"
export IMAP_SERVER="127.0.0.1"
export IMAP_PORT="1143"
export IMAP_USER="your-username"
export IMAP_PASSWORD="your-protonmail-password"
```

### Paid Accounts (Direct Access)

Paid ProtonMail accounts support direct SMTP/IMAP access:

#### Configuration
```json
{
  "SenderEmail": "your@protonmail.com",
  "SenderName": "Your Name",
  "SmtpServer": "mail.protonmail.com",
  "SmtpPort": 587,
  "SmtpUsername": "your@protonmail.com",
  "SmtpPassword": "your-protonmail-password",
  "ImapServer": "mail.protonmail.com",
  "ImapPort": 993,
  "ImapUsername": "your@protonmail.com",
  "ImapPassword": "your-protonmail-password"
}
```

#### Environment Variables
```bash
export SMTP_SERVER="mail.protonmail.com"
export SMTP_PORT="587"
export SMTP_USER="your@protonmail.com"
export SMTP_PASSWORD="your-protonmail-password"
export IMAP_SERVER="mail.protonmail.com"
export IMAP_PORT="993"
export IMAP_USER="your@protonmail.com"
export IMAP_PASSWORD="your-protonmail-password"
```

### Setup Steps for Paid Accounts
1. Enable SMTP/IMAP access in ProtonMail settings
2. Use your regular ProtonMail password (no app passwords needed)
3. Configure using `configure_service()` or environment variables

### Supported Features
- SMTP email sending with TLS encryption
- IMAP inbox checking and management
- HTML and plain text email formats
- CC/BCC recipient support
- Automatic email header decoding
- Error handling and connection testing

### Notes
- **Free accounts**: ProtonMail Bridge must be running for email access
- **Paid accounts**: Direct SMTP/IMAP access available without additional software
- **Security**: ProtonMail uses end-to-end encryption for all communications
- **Compatibility**: Works with all Email MCP features including AI collaboration

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
    "minimail-mcp": {
      "command": "python",
      "args": ["-m", "email_mcp.server"],
      "env": {
        "PYTHONPATH": "D:/Dev/repos/minimail-mcp/src"
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

