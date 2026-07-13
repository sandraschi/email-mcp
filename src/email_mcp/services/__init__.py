"""Email service implementations."""

from email_mcp.services.email_services import (
    APIEmailService,
    EmailService,
    EmailServiceConfig,
    EmailServiceFactory,
    LocalEmailService,
    SMTPEmailService,
    WebhookEmailService,
)

__all__ = [
    "APIEmailService",
    "EmailService",
    "EmailServiceConfig",
    "EmailServiceFactory",
    "LocalEmailService",
    "SMTPEmailService",
    "WebhookEmailService",
]
