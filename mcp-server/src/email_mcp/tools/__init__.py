"""
Email MCP Tools Package

This package contains the core components for email MCP server functionality.
"""

from .models import EmailService, EmailServiceConfig
from .services import (APIEmailService, LocalEmailService, SMTPEmailService,
                       WebhookEmailService)
from .tools import EmailTools, register_email_tools

__all__ = [
    # Models
    "EmailServiceConfig",
    "EmailService",

    # Services
    "SMTPEmailService",
    "APIEmailService",
    "LocalEmailService",
    "WebhookEmailService",

    # Tools
    "EmailTools",
    "register_email_tools",
]