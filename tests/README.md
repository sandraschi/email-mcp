# Email MCP Multi-Service Tests

This directory contains the comprehensive test suite for the Email MCP multi-service platform.

## 🎯 **Test Coverage**

The test suite covers all email service types:
- **SMTP/IMAP Services**: Gmail, Outlook, Yahoo, iCloud, ProtonMail
- **Transactional APIs**: SendGrid, Mailgun, Resend, Amazon SES
- **Local Testing**: MailHog, Mailpit, MailCatcher, Inbucket
- **Webhook Services**: Slack, Discord, Telegram, GitHub

## 📁 **Test Structure**

- `test_connection.py` - Basic connection and authentication tests
- `conftest.py` - Pytest configuration and comprehensive fixtures
- `run_tests.py` - Test runner script with environment detection

## 🚀 **Running Tests**

### All Tests
```bash
pytest tests/
```

### Test Runner (Recommended)
```bash
python tests/run_tests.py
```

### Selective Testing

#### Skip Network Tests
```bash
pytest -m "not network" tests/
```

#### Test Specific Service Types
```bash
# SMTP/IMAP tests only
pytest -k "smtp" tests/

# API service tests only
pytest -k "api" tests/

# Local testing services
pytest -k "local" tests/

# Webhook services
pytest -k "webhook" tests/
```

#### Run with Coverage
```bash
pytest --cov=email_mcp tests/
```

## 🏷️ **Test Categories & Markers**

| Marker | Description | Usage |
|--------|-------------|-------|
| `@pytest.mark.unit` | Unit tests (no external dependencies) | Fast, isolated tests |
| `@pytest.mark.integration` | Integration tests (service interactions) | End-to-end workflows |
| `@pytest.mark.network` | Tests requiring network access | SMTP/IMAP/API calls |
| `@pytest.mark.smtp` | SMTP-based service tests | Gmail, Outlook, etc. |
| `@pytest.mark.api` | API-based service tests | SendGrid, Mailgun, etc. |
| `@pytest.mark.local` | Local testing service tests | MailHog, Mailpit |
| `@pytest.mark.webhook` | Webhook service tests | Slack, Discord |

## 🧰 **Test Fixtures**

### Service Fixtures
- `mock_smtp_server` - Mock SMTP server for sending tests
- `mock_imap_server` - Mock IMAP server for inbox tests
- `sample_email_data` - Standard email data structure
- `sample_vrm_data` - VRM model data (for future VRoid integration)

### API Fixtures
- `sendgrid_config` - SendGrid API configuration
- `mailgun_config` - Mailgun API configuration
- `resend_config` - Resend API configuration

### Local Testing Fixtures
- `mailhog_config` - MailHog testing configuration
- `mailpit_config` - Mailpit testing configuration

### Webhook Fixtures
- `slack_config` - Slack webhook configuration
- `discord_config` - Discord webhook configuration

## ⚙️ **Environment Variables for Testing**

### SMTP/IMAP Testing
```bash
export SMTP_SERVER="smtp.gmail.com"
export SMTP_USER="test@example.com"
export SMTP_PASSWORD="test-password"
export IMAP_SERVER="imap.gmail.com"
export IMAP_USER="test@example.com"
export IMAP_PASSWORD="test-password"
```

### API Testing
```bash
export SENDGRID_API_KEY="test-sendgrid-key"
export MAILGUN_API_KEY="test-mailgun-key"
export RESEND_API_KEY="test-resend-key"
```

### Local Testing
```bash
export MAILHOG_ENABLED="true"
export MAILHOG_SMTP_HOST="localhost"
export MAILHOG_HTTP_URL="http://localhost:8025"
```

### Webhook Testing
```bash
export SLACK_WEBHOOK_URL="https://example.com/docs/slack-incoming-webhook"
export DISCORD_WEBHOOK_URL="https://discord.com/api/test-webhook"
```

## 📝 **Writing New Tests**

### 1. File Structure
```python
# tests/test_[service_type]_[feature].py
# Example: test_sendgrid_api.py, test_slack_webhook.py
```

### 2. Test Patterns

#### Unit Test Example
```python
def test_email_validation(sample_email_data):
    """Test email address validation."""
    from email_mcp.server import validate_email
    assert validate_email("test@example.com") == True
    assert validate_email("invalid-email") == False
```

#### Service Integration Test
```python
@pytest.mark.network
@pytest.mark.sendgrid
async def test_sendgrid_sending(sendgrid_config):
    """Test SendGrid email sending."""
    service = APIEmailService(sendgrid_config)
    result = await service.send_email(
        to="test@example.com",
        subject="Test",
        body="Test message"
    )
    assert result["success"] == True
```

#### Webhook Test
```python
@pytest.mark.webhook
@pytest.mark.slack
async def test_slack_webhook(slack_config):
    """Test Slack webhook integration."""
    service = WebhookEmailService(slack_config)
    result = await service.send_email(
        to="#test-channel",
        subject="Alert",
        body="Test alert message"
    )
    assert result["success"] == True
```

### 3. Best Practices

- **Use appropriate markers** for test categorization
- **Mock external services** when possible to avoid rate limits
- **Use fixtures** for common test setup and teardown
- **Test error conditions** as well as success cases
- **Document test requirements** in docstrings
- **Run tests in isolation** (no shared state between tests)

## 🔧 **Continuous Integration**

### GitHub Actions Example
```yaml
- name: Run Email MCP Tests
  run: |
    cd email-mcp
    python tests/run_tests.py

- name: Test Coverage
  run: |
    pytest --cov=email_mcp --cov-report=xml tests/
```

### Local CI Simulation
```bash
# Run all tests with coverage
pytest --cov=email_mcp --cov-report=html tests/

# Run specific service tests
pytest -m "network and (sendgrid or mailgun)" tests/

# Generate coverage report
coverage html
```

## 🐛 **Debugging Test Failures**

### Common Issues

1. **Network timeouts** - Increase timeout values or use mocks
2. **API rate limits** - Use test/sandbox API keys
3. **Service unavailability** - Check service status before running tests
4. **Environment variables** - Ensure all required env vars are set

### Debugging Commands
```bash
# Verbose test output
pytest -v -s tests/

# Debug specific test
pytest -v -s tests/test_connection.py::test_smtp_connection

# Run with pdb on failure
pytest --pdb tests/

# Show test durations
pytest --durations=10 tests/
```
