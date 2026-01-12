"""
MCP Tools for Email Management

FastMCP tool implementations for email operations.
"""

from typing import Any, Dict, List, Optional, Union

from fastmcp import Tool
from pydantic import Field

from .models import EmailServiceConfig
from .services import (APIEmailService, EmailService, LocalEmailService,
                       SMTPEmailService, WebhookEmailService)


class EmailTools:
    """MCP tools for email operations."""

    def __init__(self, services: Dict[str, EmailService]):
        self.services = services

    def _get_service(self, service_name: str) -> Optional[EmailService]:
        """Get service by name."""
        return self.services.get(service_name)

    def _create_service(self, config: EmailServiceConfig) -> EmailService:
        """Create service instance from config."""
        if config.type == "smtp":
            return SMTPEmailService(config)
        elif config.type == "api":
            return APIEmailService(config)
        elif config.type == "local":
            return LocalEmailService(config)
        elif config.type == "webhook":
            return WebhookEmailService(config)
        else:
            raise ValueError(f"Unsupported service type: {config.type}")

    async def send_email_tool(self,
                              to: Union[str, List[str]] = Field(..., description="Recipient email address(es)"),
                              subject: str = Field(..., description="Email subject line"),
                              body: str = Field(..., description="Plain text email body"),
                              service: str = Field("default", description="Email service to use"),
                              html: Optional[str] = Field(None, description="Optional HTML email body"),
                              cc: Optional[List[str]] = Field(None, description="Optional CC recipients"),
                              bcc: Optional[List[str]] = Field(None, description="Optional BCC recipients")) -> Dict[str, Any]:
        """Send an email via specified email service."""
        service_obj = self._get_service(service)
        if not service_obj:
            return {"success": False, "error": f"Service '{service}' not found"}

        return await service_obj.send_email(to, subject, body, html, cc, bcc)

    async def check_inbox_tool(self,
                               service: str = Field("default", description="Email service to check"),
                               folder: str = Field("INBOX", description="Mail folder name"),
                               limit: int = Field(10, description="Maximum emails to return"),
                               unread_only: bool = Field(False, description="Only return unread emails")) -> Dict[str, Any]:
        """Check inbox via specified email service."""
        service_obj = self._get_service(service)
        if not service_obj:
            return {"success": False, "error": f"Service '{service}' not found"}

        return await service_obj.check_inbox(folder, limit, unread_only)

    async def email_status_tool(self,
                                service: Optional[str] = Field(None, description="Specific service to test, or None for all")) -> Dict[str, Any]:
        """Get email service status and test connectivity."""
        if service:
            service_obj = self._get_service(service)
            if not service_obj:
                return {"server": "email-mcp", "error": f"Service '{service}' not found"}

            result = await service_obj.test_connection()
            return {
                "server": "email-mcp",
                "version": "0.2.0",
                "services": {service: result}
            }

        # Test all services
        results = {}
        for name, service_obj in self.services.items():
            try:
                results[name] = await service_obj.test_connection()
            except Exception as e:
                results[name] = {"connected": False, "error": str(e)}

        return {
            "server": "email-mcp",
            "version": "0.2.0",
            "services": results,
            "total_services": len(results),
            "configured_services": len([r for r in results.values() if r.get("connected")]),
            "connected_services": len([r for r in results.values() if r.get("connected")])
        }

    async def configure_service_tool(self,
                                    name: str = Field(..., description="Unique name for the service"),
                                    type: str = Field(..., description="Service type: smtp, api, local, webhook"),
                                    config: Dict[str, Any] = Field(..., description="Service-specific configuration"),
                                    enabled: bool = Field(True, description="Whether service should be enabled")) -> Dict[str, Any]:
        """Configure a new email service dynamically."""
        if name in self.services:
            return {"success": False, "service": name, "error": "Service already exists"}

        try:
            config_obj = EmailServiceConfig(name=name, type=type, enabled=enabled, config=config)
            service = self._create_service(config_obj)
            self.services[name] = service

            return {"success": True, "service": name, "type": type, "message": "Service configured successfully"}

        except Exception as e:
            return {"success": False, "service": name, "error": str(e)}

    async def list_services_tool(self) -> Dict[str, Any]:
        """List all configured email services."""
        services_info = {}
        for name, service in self.services.items():
            services_info[name] = {
                "type": service.config.type,
                "enabled": service.config.enabled,
                "configured": True,  # All services in dict are configured
                "description": self._get_service_description(service.config.type)
            }

        return {
            "services": services_info,
            "count": len(services_info),
            "enabled_count": len([s for s in services_info.values() if s["enabled"]]),
            "types": list(set(s["type"] for s in services_info.values()))
        }

    def _get_service_description(self, service_type: str) -> str:
        """Get human-readable description for service type."""
        descriptions = {
            "smtp": "SMTP/IMAP service (Gmail, Outlook, Yahoo, etc.)",
            "api": "API-based service (SendGrid, Mailgun, Resend)",
            "local": "Local testing service (MailHog, Mailpit)",
            "webhook": "Webhook service (Slack, Discord)"
        }
        return descriptions.get(service_type, f"{service_type} service")

    async def email_help_tool(self) -> Dict[str, Any]:
        """Get help and usage information for email MCP tools."""
        return {
            "server": "email-mcp",
            "version": "0.2.0",
            "description": "Multi-service email platform supporting SMTP/IMAP, transactional APIs, local testing, and webhook integrations",
            "supported_services": {
                "smtp": "SMTP/IMAP services like Gmail, Outlook, Yahoo with secure authentication",
                "api": "Transactional email APIs like SendGrid, Mailgun, Resend with high deliverability",
                "local": "Local testing services like MailHog, Mailpit for development",
                "webhook": "Webhook integrations for Slack, Discord, Telegram notifications"
            },
            "tools": [
                {
                    "name": "send_email",
                    "description": "Send emails via configured services",
                    "parameters": ["to", "subject", "body", "service", "html", "cc", "bcc"]
                },
                {
                    "name": "check_inbox",
                    "description": "Check inbox for new emails",
                    "parameters": ["service", "folder", "limit", "unread_only"]
                },
                {
                    "name": "email_status",
                    "description": "Test service connectivity and get status",
                    "parameters": ["service"]
                },
                {
                    "name": "configure_service",
                    "description": "Add new email service configuration",
                    "parameters": ["name", "type", "config", "enabled"]
                },
                {
                    "name": "list_services",
                    "description": "List all configured services",
                    "parameters": []
                }
            ],
            "examples": [
                "Send email: send_email(to='user@example.com', subject='Hello', body='Test message')",
                "Check inbox: check_inbox(service='gmail', unread_only=True)",
                "Configure Gmail: configure_service(name='gmail', type='smtp', config={'smtp_server': 'smtp.gmail.com', ...})"
            ],
            "notes": [
                "API services typically don't support inbox checking",
                "Local services provide web UIs for email inspection",
                "Webhook services convert emails to chat notifications",
                "SMTP services require proper authentication (App Passwords for Gmail)"
            ]
        }


# Tool registration function
def register_email_tools(server, services: Dict[str, EmailService]):
    """Register email tools with MCP server."""
    tools = EmailTools(services)

    @server.tool()
    async def send_email(to: Union[str, List[str]], subject: str, body: str,
                        service: str = "default", html: Optional[str] = None,
                        cc: Optional[List[str]] = None, bcc: Optional[List[str]] = None):
        """Send an email via specified email service."""
        return await tools.send_email_tool(to, subject, body, service, html, cc, bcc)

    @server.tool()
    async def check_inbox(service: str = "default", folder: str = "INBOX",
                         limit: int = 10, unread_only: bool = False):
        """Check inbox via specified email service."""
        return await tools.check_inbox_tool(service, folder, limit, unread_only)

    @server.tool()
    async def email_status(service: Optional[str] = None):
        """Get email service status and test connectivity."""
        return await tools.email_status_tool(service)

    @server.tool()
    async def configure_service(name: str, type: str, config: Dict[str, Any], enabled: bool = True):
        """Configure a new email service dynamically."""
        return await tools.configure_service_tool(name, type, config, enabled)

    @server.tool()
    async def list_services():
        """List all configured email services."""
        return await tools.list_services_tool()

    @server.tool()
    async def email_help():
        """Get help and usage information for email MCP tools and services."""
        return await tools.email_help_tool()