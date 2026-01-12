"""
Email MCP Server - Multi-Service Email Platform

A comprehensive email MCP server supporting multiple email services including:
- Standard SMTP/IMAP providers (Gmail, Outlook, Yahoo, iCloud, ProtonMail)
- Transactional email APIs (SendGrid, Mailgun, Postmark, Amazon SES, Resend)
- Local testing services (MailHog, Mailpit, MailCatcher, Inbucket)
- Dev/webhook services (Slack, Discord, Telegram, GitHub)

This server exposes tools for:
- send_email: Send emails via multiple service types
- check_inbox: Check inbox via IMAP or service-specific APIs
- email_status: Get server configuration and connectivity status
- configure_service: Configure different email services dynamically
- list_services: List available and configured email services

Configuration supports both environment variables and dynamic service configuration.
"""

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional, Union

from fastmcp import FastMCP

from .tools import EmailTools, register_email_tools
from .tools.models import EmailServiceConfig
from .tools.services import (APIEmailService, LocalEmailService,
                             SMTPEmailService, WebhookEmailService)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
app = FastMCP("Email MCP Server")


# Initialize services from environment variables
def initialize_services() -> Dict[str, Any]:
    """Initialize email services from environment variables."""
    services = {}

    # SMTP service (default)
    if os.getenv("SMTP_USER") and os.getenv("SMTP_PASSWORD"):
        smtp_config = EmailServiceConfig(
            name="default",
            type="smtp",
            enabled=True,
            config={
                "smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
                "smtp_port": int(os.getenv("SMTP_PORT", "587")),
                "smtp_user": os.getenv("SMTP_USER"),
                "smtp_password": os.getenv("SMTP_PASSWORD"),
                "smtp_from": os.getenv("SMTP_FROM", os.getenv("SMTP_USER")),
                "imap_server": os.getenv("IMAP_SERVER", "imap.gmail.com"),
                "imap_port": int(os.getenv("IMAP_PORT", "993")),
                "imap_user": os.getenv("IMAP_USER", os.getenv("SMTP_USER")),
                "imap_password": os.getenv("IMAP_PASSWORD", os.getenv("SMTP_PASSWORD")),
            }
        )
        services["default"] = SMTPEmailService(smtp_config)

    # API services
    api_services = {
        "sendgrid": {"api_key": os.getenv("SENDGRID_API_KEY"), "service_type": "sendgrid"},
        "mailgun": {"api_key": os.getenv("MAILGUN_API_KEY"), "service_type": "mailgun"},
        "resend": {"api_key": os.getenv("RESEND_API_KEY"), "service_type": "resend"},
    }

    for service_name, config_data in api_services.items():
        if config_data["api_key"]:
            api_config = EmailServiceConfig(
                name=service_name,
                type="api",
                enabled=True,
                config={
                    **config_data,
                    "api_url": os.getenv(f"{service_name.upper()}_API_URL"),
                    "from_email": os.getenv(f"{service_name.upper()}_FROM_EMAIL"),
                }
            )
            services[service_name] = APIEmailService(api_config)

    # Webhook services
    webhook_services = {
        "slack": {"webhook_url": os.getenv("SLACK_WEBHOOK_URL"), "service_type": "slack"},
        "discord": {"webhook_url": os.getenv("DISCORD_WEBHOOK_URL"), "service_type": "discord"},
    }

    for service_name, config_data in webhook_services.items():
        if config_data["webhook_url"]:
            webhook_config = EmailServiceConfig(
                name=service_name,
                type="webhook",
                enabled=True,
                config=config_data
            )
            services[service_name] = WebhookEmailService(webhook_config)

    # Local testing services
    if os.getenv("MAILHOG_SMTP_SERVER"):
        mailhog_config = EmailServiceConfig(
            name="mailhog",
            type="local",
            enabled=True,
            config={
                "smtp_server": os.getenv("MAILHOG_SMTP_SERVER", "localhost"),
                "smtp_port": int(os.getenv("MAILHOG_SMTP_PORT", "1025")),
                "http_url": os.getenv("MAILHOG_HTTP_URL", "http://localhost:8025"),
                "service_type": "mailhog",
            }
        )
        services["mailhog"] = LocalEmailService(mailhog_config)

    return services


# Initialize email tools
services = initialize_services()
email_tools = EmailTools(services)

# Register tools with the server
register_email_tools(app, services)


if __name__ == "__main__":
    # Run the MCP server
    import mcp

    mcp.run(app)