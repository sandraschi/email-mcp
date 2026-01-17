# Email MCP Server - Comprehensive User Guide v0.3.0

## Overview & Quick Start

The Email MCP Server provides enterprise-grade email capabilities across multiple protocols and services. This guide covers everything from basic usage to advanced automation workflows.

### Core Concepts
- **Multi-Service Support**: SMTP, API services, local testing, and webhook integrations
- **Dynamic Configuration**: Runtime service setup without server restarts
- **Conversational Responses**: Natural language feedback for all operations
- **FastMCP 2.14.3 Compliance**: Modern protocol support with async operations

## Essential Operations

### 1. Email Sending Fundamentals

#### Basic Text Email
```python
# Send a simple email via default SMTP service
send_email(
    to="user@example.com",
    subject="Hello from Email MCP",
    body="This is a test message sent via the Email MCP Server."
)
```

#### HTML Email with Rich Formatting
```python
send_email(
    to="customer@company.com",
    subject="Welcome to Our Platform",
    body="Please view this email in HTML mode for the best experience.",
    html="""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h1 style="color: #333;">Welcome!</h1>
        <p>Thank you for joining our platform. Here's what you can do:</p>
        <ul>
            <li>Access your dashboard</li>
            <li>Manage your profile</li>
            <li>View analytics</li>
        </ul>
        <a href="https://app.example.com" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Get Started</a>
    </div>
    """
)
```

#### Advanced Recipient Handling
```python
# Multiple recipients with CC/BCC
send_email(
    to=["primary@company.com", "team@company.com"],
    cc=["manager@company.com"],
    bcc=["admin@company.com", "audit@company.com"],
    subject="Q4 Planning Meeting",
    body="Please review the attached Q4 planning document and prepare your input for tomorrow's meeting."
)
```

### 2. Service Selection Strategies

#### Transactional Email Services
```python
# High-volume marketing campaign
send_email(
    to=subscriber.email,
    subject="Your Weekly Newsletter",
    html=newsletter_template.render(content=weekly_content),
    service="sendgrid"  # Optimized for bulk sending
)

# Critical system notifications
send_email(
    to=["oncall@company.com", "#alerts"],
    subject="PRODUCTION ALERT: API Down",
    body=f"API response time > 5s for {duration}. Immediate investigation required.",
    service="slack"  # Real-time team notifications
)

# Customer support tickets
send_email(
    to=customer.email,
    subject=f"Support Ticket #{ticket.id} - {ticket.subject}",
    html=support_template.render(ticket=ticket),
    service="mailgun"  # Webhook integration for tracking
)
```

#### Development & Testing
```python
# Local development testing
send_email(
    to="developer@local.dev",
    subject="Debug Information",
    body=f"User ID: {user.id}\nError: {error.message}\nStack: {traceback.format_exc()}",
    service="mailhog"  # Local testing server
)

# CI/CD notifications
send_email(
    to="#deployments",
    subject=f"🚀 Deployment {version} Complete",
    body=f"Successfully deployed {version} to production environment.\nBuild: {build_id}\nDuration: {duration}s",
    service="discord"  # Team collaboration platform
)
```

### 3. Advanced Inbox Management

#### Intelligent Email Filtering
```python
# Unread emails from VIP senders
vip_emails = check_inbox(
    unread_only=True,
    limit=50
)

important_emails = [
    email for email in vip_emails['emails']
    if email['from'] in VIP_SENDERS
]

print(f"Found {len(important_emails)} important unread emails")
```

#### Time-based Email Queries
```python
from datetime import datetime, timedelta

# Emails from today
today = datetime.now().strftime("%Y-%m-%d")
todays_emails = check_inbox(after_date=today)

# Emails from last week
week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
weekly_emails = check_inbox(after_date=week_ago)

# Meeting-related emails this month
this_month = datetime.now().strftime("%Y-%m")
meetings = check_inbox(
    after_date=f"{this_month}-01",
    limit=100
)

meeting_emails = [
    email for email in meetings['emails']
    if any(keyword in email['subject'].lower() for keyword in ['meeting', 'call', 'sync'])
]
```

#### Multi-folder Email Processing
```python
# Process different email folders
folders_to_check = ['INBOX', 'Sent', 'Archive']

for folder in folders_to_check:
    result = check_inbox(folder=folder, limit=20)
    print(f"{folder}: {result['count']} emails")

    # Archive old emails
    if folder == 'INBOX':
        old_emails = [
            email for email in result['emails']
            if email['date'] < (datetime.now() - timedelta(days=30)).isoformat()
        ]
        for email in old_emails:
            # Note: Actual move_to_folder would be implemented based on IMAP capabilities
            pass
```

## Service Configuration & Management

### 4. Dynamic Service Configuration

#### Gmail SMTP Setup
```python
configure_service(
    name="gmail-personal",
    type="smtp",
    config={
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "smtp_user": "your.email@gmail.com",
        "smtp_password": "your-app-password",  # Never use regular password
        "imap_server": "imap.gmail.com",
        "imap_port": 993,
        "imap_user": "your.email@gmail.com",
        "imap_password": "your-app-password"
    }
)
```

#### SendGrid Transactional Email
```python
configure_service(
    name="sendgrid-prod",
    type="api",
    config={
        "api_key": "SG.your-sendgrid-api-key-here",
        "api_url": "https://api.sendgrid.com/v3/mail/send",
        "from_email": "noreply@yourcompany.com",
        "service_type": "sendgrid"
    }
)
```

#### Slack Webhook Integration
```python
configure_service(
    name="slack-alerts",
    type="webhook",
    config={
        "webhook_url": "https://example.com/docs/slack-incoming-webhook",
        "service_type": "slack"
    }
)
```

#### Local Development Environment
```python
configure_service(
    name="mailhog-dev",
    type="local",
    config={
        "smtp_server": "localhost",
        "smtp_port": 1025,
        "http_url": "http://localhost:8025",
        "service_type": "mailhog"
    }
)
```

### 5. Service Monitoring & Health Checks

#### Comprehensive Status Monitoring
```python
# Check all services health
status = email_status()
print(f"Server Version: {status['version']}")
print(f"Total Services: {status['total_services']}")
print(f"Connected Services: {status['connected_services']}")

# Detailed service analysis
for service_name, service_info in status['services'].items():
    status_indicator = "✅" if service_info['connected'] else "❌"
    print(f"{status_indicator} {service_name}: {service_info['type']}")

    if not service_info['connected'] and service_info.get('error'):
        print(f"   Error: {service_info['error']}")
```

#### Service Discovery
```python
# List all available services
services = list_services()

print("Available Email Services:")
print("=" * 40)

for name, info in services['services'].items():
    status = "✅ Enabled" if info['enabled'] else "⏸️  Disabled"
    configured = "✅ Configured" if info['configured'] else "❌ Not Configured"

    print(f"{name}")
    print(f"  Type: {info['type']}")
    print(f"  Status: {status}")
    print(f"  Configuration: {configured}")
    print(f"  Description: {info['description']}")
    print()
```

## Advanced Workflows & Automation

### 6. Email Processing Automation

#### Intelligent Email Triage
```python
def process_inbox_automation():
    """Automated email processing workflow"""

    # Get unread emails
    unread = check_inbox(unread_only=True, limit=100)

    for email in unread['emails']:
        # Categorize by sender
        if email['from'] in URGENT_SENDERS:
            # Forward to management
            send_email(
                to="management@company.com",
                subject=f"URGENT: {email['subject']}",
                body=f"Urgent email from {email['from']}\n\n{email.get('body', 'No body content')}",
                service="sendgrid"
            )

        elif any(spam_word in email['subject'].lower() for spam_word in SPAM_KEYWORDS):
            # Mark as spam (would integrate with IMAP operations)
            pass

        elif email['from'].endswith('@github.com'):
            # GitHub notifications
            send_email(
                to="#dev-team",
                subject=f"🐙 {email['subject']}",
                body=f"GitHub notification:\n{email.get('body', '')}",
                service="slack"
            )

# Run automated processing
process_inbox_automation()
```

#### Customer Communication Sequences
```python
def send_customer_sequence(customer_email, customer_name):
    """Multi-step customer communication"""

    # Welcome email
    send_email(
        to=customer_email,
        subject="Welcome to Our Service!",
        html=welcome_template.render(name=customer_name),
        service="sendgrid"
    )

    # Follow-up after 3 days
    # (Would be scheduled via external job system)

    # Onboarding checklist after 1 week
    # (Would be scheduled via external job system)

def send_abandoned_cart_recovery(cart_data):
    """E-commerce recovery automation"""

    send_email(
        to=cart_data['customer_email'],
        subject="Your Cart is Waiting!",
        html=cart_recovery_template.render(
            items=cart_data['items'],
            total=cart_data['total'],
            cart_url=f"https://store.com/cart/{cart_data['cart_id']}"
        ),
        service="mailgun"  # Better for e-commerce tracking
    )
```

### 7. Error Handling & Resilience

#### Robust Email Operations
```python
def send_email_with_fallback(to, subject, body, primary_service="sendgrid"):
    """Send email with automatic service fallback"""

    services_to_try = [primary_service, "mailgun", "resend", "smtp"]

    for service in services_to_try:
        try:
            result = send_email(
                to=to,
                subject=subject,
                body=body,
                service=service
            )

            if result.get('success'):
                print(f"Email sent successfully via {service}")
                return result
            else:
                print(f"Failed via {service}: {result.get('error')}")

        except Exception as e:
            print(f"Exception with {service}: {str(e)}")
            continue

    # Final fallback - notify administrators
    send_email(
        to="admin@company.com",
        subject="CRITICAL: Email Delivery Failure",
        body=f"Failed to send email to {to} via all services.\nSubject: {subject}",
        service="slack"  # Critical notifications
    )

    return {"success": False, "error": "All services failed"}
```

#### Connection Health Monitoring
```python
def monitor_email_services():
    """Continuous service health monitoring"""

    while True:
        status = email_status()

        unhealthy_services = [
            name for name, info in status['services'].items()
            if not info['connected']
        ]

        if unhealthy_services:
            alert_message = f"Email services unhealthy: {', '.join(unhealthy_services)}"

            send_email(
                to=["admin@company.com", "#alerts"],
                subject="EMAIL SERVICE ALERT",
                body=alert_message,
                service="slack"
            )

        # Check every 5 minutes
        time.sleep(300)
```

## Configuration Templates

### 8. Environment Setup

#### Production Environment
```bash
# Core SMTP (fallback)
export SMTP_SERVER="smtp.company.com"
export SMTP_PORT="587"
export SMTP_USER="noreply@company.com"
export SMTP_PASSWORD="secure-password"

# SendGrid for transactional emails
export SENDGRID_API_KEY="SG.secure-api-key"
export SENDGRID_FROM_EMAIL="noreply@company.com"

# Mailgun for marketing
export MAILGUN_API_KEY="key-secure-mailgun-key"
export MAILGUN_DOMAIN="company.com"

# Slack for team notifications
export SLACK_WEBHOOK_URL="https://example.com/docs/slack-incoming-webhook"

# Discord for community updates
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/1234567890123456789/abcdef123456789"
```

#### Development Environment
```bash
# MailHog for local testing
export MAILHOG_ENABLED="true"
export MAILHOG_SMTP_HOST="localhost"
export MAILHOG_SMTP_PORT="1025"
export MAILHOG_HTTP_URL="http://localhost:8025"

# Test SendGrid (optional)
export SENDGRID_API_KEY="SG.test-key"
export SENDGRID_FROM_EMAIL="test@company.dev"
```

### 9. Common Patterns & Best Practices

#### Email Template Management
```python
class EmailTemplates:
    """Centralized email template management"""

    @staticmethod
    def welcome_email(customer_name, company_name):
        return f"""
        Subject: Welcome to {company_name}!

        Dear {customer_name},

        Welcome to {company_name}! We're excited to have you on board.

        Here's what you can do to get started:
        1. Complete your profile
        2. Explore our features
        3. Connect with the community

        Best regards,
        The {company_name} Team
        """

    @staticmethod
    def password_reset_html(user_email, reset_token):
        return f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>Password Reset Request</h2>
            <p>You requested a password reset for {user_email}.</p>
            <p><a href="https://app.company.com/reset?token={reset_token}"
                  style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none;">
                Reset Password
            </a></p>
            <p>This link expires in 24 hours.</p>
        </div>
        """

# Usage
send_email(
    to=customer.email,
    subject="Welcome!",
    body=EmailTemplates.welcome_email(customer.name, "Our Company"),
    service="sendgrid"
)
```

#### Batch Email Operations
```python
def send_bulk_newsletter(subscribers, newsletter_content):
    """Send newsletter to multiple subscribers"""

    successful = 0
    failed = 0

    for subscriber in subscribers:
        try:
            send_email(
                to=subscriber['email'],
                subject=newsletter_content['subject'],
                html=newsletter_content['html_template'].render(
                    name=subscriber['name'],
                    preferences=subscriber['preferences']
                ),
                service="sendgrid"
            )
            successful += 1

        except Exception as e:
            print(f"Failed to send to {subscriber['email']}: {e}")
            failed += 1

    # Send summary report
    send_email(
        to="marketing@company.com",
        subject="Newsletter Send Complete",
        body=f"Newsletter sent successfully to {successful} subscribers.\nFailed: {failed}",
        service="mailgun"
    )
```

## Troubleshooting Guide

### 10. Common Issues & Solutions

#### Authentication Problems
```python
# Gmail App Password Setup
# 1. Enable 2FA on your Google account
# 2. Go to https://myaccount.google.com/apppasswords
# 3. Generate app password for "Mail"
# 4. Use the 16-character password (ignore spaces)

configure_service(
    name="gmail-fixed",
    type="smtp",
    config={
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "smtp_user": "your.email@gmail.com",
        "smtp_password": "abcd-efgh-ijkl-mnop",  # 16-char app password
    }
)
```

#### Connection Issues
```python
# Test service connectivity
status = email_status()
for service, info in status['services'].items():
    if not info['connected']:
        print(f"Service {service} failed: {info.get('error', 'Unknown error')}")

# Try alternative ports/encryption
configure_service(
    name="outlook-ssl",
    type="smtp",
    config={
        "smtp_server": "smtp-mail.outlook.com",
        "smtp_port": 465,  # SSL instead of 587 (TLS)
        "smtp_user": "your.email@outlook.com",
        "smtp_password": "your-password"
    }
)
```

#### Rate Limiting
```python
import time

def send_with_rate_limit(emails, max_per_minute=50):
    """Send emails with rate limiting"""

    for i, email_data in enumerate(emails):
        send_email(**email_data)

        # Rate limiting
        if (i + 1) % max_per_minute == 0:
            print(f"Sent {i + 1} emails, pausing for rate limit...")
            time.sleep(60)  # Wait 1 minute
```

## Performance Optimization

### 11. Advanced Configuration

#### Connection Pooling
```python
# For high-volume applications
import asyncio

async def send_bulk_emails_async(email_list):
    """Send multiple emails concurrently"""

    # Limit concurrency to avoid overwhelming services
    semaphore = asyncio.Semaphore(10)  # Max 10 concurrent sends

    async def send_with_limit(email_data):
        async with semaphore:
            return await send_email(**email_data)

    # Send all emails concurrently with limit
    tasks = [send_with_limit(email) for email in email_list]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    return results
```

#### Template Pre-compilation
```python
from jinja2 import Template

class EmailRenderer:
    """Pre-compile email templates for performance"""

    def __init__(self):
        self.templates = {}

    def load_template(self, name, template_str):
        """Pre-compile Jinja2 template"""
        self.templates[name] = Template(template_str)

    def render(self, name, **context):
        """Render pre-compiled template"""
        return self.templates[name].render(**context)

# Usage
renderer = EmailRenderer()
renderer.load_template('welcome', welcome_email_template)

send_email(
    to=user.email,
    subject="Welcome!",
    html=renderer.render('welcome', user=user),
    service="sendgrid"
)
```

This comprehensive guide covers the full spectrum of Email MCP Server capabilities. From basic email sending to complex automation workflows, the server provides enterprise-grade email functionality with the flexibility of multiple service providers and the intelligence of AI-driven operations.