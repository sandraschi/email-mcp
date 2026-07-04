"""All EmailMCP MCP tool registrations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog
from fastmcp import FastMCP

from email_mcp.services.email_services import (
    APIEmailService,
    EmailServiceConfig,
    EmailServiceFactory,
    LocalEmailService,
    SMTPEmailService,
    WebhookEmailService,
)

if TYPE_CHECKING:
    from email_mcp.server import EmailMCP

logger = structlog.get_logger(__name__)

def register_tools(mcp: FastMCP, server: EmailMCP) -> None:
    """Register all email tools with the FastMCP server.

    This method registers tools for:
    - send_email: Send emails via multiple services
    - check_inbox: Check inbox via multiple services
    - email_status: Check service configuration and connectivity
    - configure_service: Configure additional email services
    - list_services: List available email services
    """

    @mcp.tool()
    async def send_email(
        to: str | list[str],
        subject: str,
        body: str,
        service: str = "default",
        html: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        attachments: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Send an email via specified email service.

        Sends an email using the specified email service. Supports SMTP, API-based services,
        local testing services, and webhook integrations. Automatically detects service
        capabilities and uses the appropriate sending method.

        Args:
            to: Recipient email address(es). Can be:
                - Single address: "user@example.com"
                - Comma-separated: "user1@example.com, user2@example.com"
                - List: ["user1@example.com", "user2@example.com"]
            subject: Email subject line. Required.
            body: Plain text email body. Required. This serves as the fallback
                for email clients that don't support HTML.
            service: Email service to use. Options:
                - "default": Default SMTP/IMAP service (from env vars)
                - "sendgrid": SendGrid transactional email
                - "mailgun": Mailgun transactional email
                - "resend": Resend transactional email
                - "mailhog": Local MailHog testing service
                - "slack": Send to Slack webhook
                - "discord": Send to Discord webhook
                - Custom service names configured via EMAIL_SERVICES
            html: Optional HTML email body. If provided, the email will be sent
                as multipart/alternative with both text and HTML versions.
                Example: "<h1>Title</h1><p>Content</p>"
            cc: Optional CC (carbon copy) recipients. Same format as 'to'.
            bcc: Optional BCC (blind carbon copy) recipients. Same format as 'to'.
            attachments: Optional list of attachment dicts. Each dict has:
                - filename: str (required)
                - content: str (base64-encoded or raw text, required)
                - content_type: str (optional, default "application/octet-stream")

        Returns:
            Dictionary with service-specific results:
            {
                "success": bool,      # True if email sent successfully
                "status": str,        # "sent" on success
                "service": str,       # Service used
                "to": str,            # Recipient address(es)
                "subject": str,       # Email subject
                "error": str          # Error message if success is False
            }

        Examples:
            # Send via default SMTP service
            send_email(
                to="user@example.com",
                subject="Hello",
                body="This is a test email"
            )

            # Send via SendGrid
            send_email(
                to="user@example.com",
                subject="Welcome",
                body="Welcome to our service",
                service="sendgrid",
                html="<h1>Welcome!</h1><p>Thanks for joining.</p>"
            )

            # Send to Slack webhook
            send_email(
                to="general",
                subject="Alert",
                body="System alert message",
                service="slack"
            )

        Notes:
            - Service availability depends on configuration
            - API services may have different rate limits and features
            - Local testing services don't send real emails
            - Webhook services convert emails to chat messages
        """
        if service not in server.services:
            available_services = list(server.services.keys())
            return {
                "success": False,
                "error": f"Service '{service}' not available. Available services: {available_services}",
            }

        email_service = server.services[service]
        result = await email_service.send_email(to, subject, body, html, cc, bcc, attachments)

        if result.get("success"):
            logger.info("Email sent successfully", service=service, to=to, subject=subject)
            result["message"] = f"Email '{subject}' sent successfully to {to} via {service} service"
        else:
            logger.error("Failed to send email", service=service, error=result.get("error"))
            result["message"] = f"Failed to send email: {result.get('error')}"

        return result

    @mcp.tool()
    async def check_inbox(
        service: str = "default",
        folder: str = "INBOX",
        limit: int = 10,
        unread_only: bool = False,
        from_contains: str | None = None,
        subject_contains: str | None = None,
    ) -> dict[str, Any]:
        """Check inbox via specified email service.

        Retrieves emails from the specified service and folder. Supports IMAP-based services,
        local testing services with web APIs, and service-specific inbox checking.

        Args:
            service: Email service to check. Options:
                - "default": Default IMAP service (from env vars)
                - "mailhog": Local MailHog testing service
                - "mailpit": Local Mailpit testing service
                - Custom service names that support inbox checking
            folder: Mail folder name to check. Default: "INBOX". Common folders:
                - "INBOX": Main inbox folder
                - "Sent": Sent items folder
                - "Drafts": Draft messages folder
                - "Trash": Deleted messages folder
                Folder names are case-sensitive and provider-specific.
            limit: Maximum number of emails to return. Default: 10.
            unread_only: If True, only returns unread emails. Default: False.
            from_contains: Optional case-insensitive substring filter on From (IMAP scans recent mail).
            subject_contains: Optional case-insensitive substring filter on Subject.

        Returns:
            Dictionary with service-specific results:
            {
                "success": bool,      # True if inbox check succeeded
                "emails": [           # List of email dictionaries
                    {
                        "id": str,            # Message ID
                        "subject": str,       # Email subject
                        "from": str,          # Sender address
                        "date": str,          # Email date
                        "read": bool          # Read status
                    }
                ],
                "count": int,         # Number of emails returned
                "service": str,       # Service used
                "folder": str,        # Folder checked
                "error": str          # Error message if success is False
            }

        Examples:
            # Check default IMAP inbox
            check_inbox()
            # Returns: {"success": True, "emails": [...], "count": 10, "service": "default"}

            # Check MailHog testing inbox
            check_inbox(service="mailhog", limit=20)
            # Returns emails from local testing service

            # Check unread emails only
            check_inbox(unread_only=True, limit=5)

        Notes:
            - Not all services support inbox checking (API/webhook services typically don't)
            - Local testing services provide web UIs for viewing emails
            - IMAP services support standard folder names
            - Results are sorted with most recent first
        """
        if service not in server.services:
            available_services = list(server.services.keys())
            return {
                "success": False,
                "error": f"Service '{service}' not available. Available services: {available_services}",
            }

        email_service = server.services[service]
        result = await email_service.check_inbox(folder, limit, unread_only, from_contains, subject_contains)

        if result.get("success"):
            count = result.get("count", 0)
            logger.info("Inbox checked", service=service, count=count, folder=folder)
            result["message"] = f"Found {count} emails in {folder} via {service} service"
            result["folder"] = folder
            if from_contains or subject_contains:
                result["filters"] = {
                    "from_contains": from_contains,
                    "subject_contains": subject_contains,
                }
            # Layer 2: safety-wrap email subject/from/body for prompt injection
            result["emails"] = wrap_untrusted_list(result.get("emails", []), source="inbox")
        else:
            logger.error("Failed to check inbox", service=service, error=result.get("error"))
            result["message"] = f"Failed to check inbox: {result.get('error')}"

        return result

    @mcp.tool()
    async def mailing_lists_catalog() -> dict[str, Any]:
        """MAILING_LISTS_CATALOG -- List named mailing-list presets from EMAIL_MCP_MAILING_LISTS (JSON).

        Configure labels/folders once (e.g. Gmail filter â†’ IMAP folder), then use mailing_list_latest(id).

        Returns:
            success, entries[] with id, service, folder, limit, unread_only, from_contains, subject_contains;
            or error if unset/invalid JSON.
        """
        entries, err = load_mailing_list_entries()
        if err and not entries:
            return {"success": False, "error": err, "entries": []}
        rows = [e.model_dump() for e in entries]
        return {
            "success": True,
            "count": len(rows),
            "entries": rows,
            "message": f"{len(rows)} mailing list(s) configured",
        }

    @mcp.tool()
    async def mailing_list_latest(
        list_id: str,
        limit: int | None = None,
        unread_only: bool | None = None,
    ) -> dict[str, Any]:
        """MAILING_LIST_LATEST -- Fetch newest messages for a preset id (see mailing_lists_catalog).

        Loads folder/service/filters from EMAIL_MCP_MAILING_LISTS. Typical use: newsletter drops in a
        dedicated IMAP folder (Alpha Signal, etc.). Optional limit/unread_only override entry defaults.

        Args:
            list_id: Preset id from catalog (e.g. alphasignal).
            limit: Override max messages (default: from preset, usually 5).
            unread_only: Override UNSEEN-only (default: from preset, usually True for newest drop).

        Returns:
            Same shape as check_inbox plus list_id and preset fields.
        """
        entries, err = load_mailing_list_entries()
        if err and not entries:
            return {"success": False, "error": err, "emails": [], "count": 0}

        entry = next((e for e in entries if e.id == list_id.strip()), None)
        if entry is None:
            ids = [e.id for e in entries]
            return {
                "success": False,
                "error": f"No mailing list id {list_id!r}. Configured ids: {ids}",
                "emails": [],
                "count": 0,
            }

        if entry.service not in server.services:
            return {
                "success": False,
                "error": f"Service {entry.service!r} not available for list {entry.id!r}",
                "emails": [],
                "count": 0,
            }

        lim = entry.limit if limit is None else limit
        unread = entry.unread_only if unread_only is None else unread_only

        email_service = server.services[entry.service]
        result = await email_service.check_inbox(
            entry.folder,
            lim,
            unread,
            entry.from_contains,
            entry.subject_contains,
        )

        result["list_id"] = entry.id
        result["preset"] = entry.model_dump()
        if result.get("success"):
            result["message"] = f"List {entry.id!r}: {result.get('count', 0)} message(s) from {entry.folder}"
            result["emails"] = wrap_untrusted_list(result.get("emails", []), source="mailing_list")
        return result

    @mcp.tool()
    async def email_status(service: str | None = None) -> dict[str, Any]:
        """Get email service status and test connectivity.

        Tests connectivity for specified service or all configured services.
        Verifies that credentials are correct and services are reachable.

        Args:
            service: Specific service to test, or None for all services.

        Returns:
            Dictionary with service status information:
            {
                "server": str,           # Server name
                "version": str,          # Server version
                "services": {            # Service-specific status
                    "service_name": {
                        "configured": bool,
                        "connected": bool,
                        "error": str,        # Error message if connection failed
                        "type": str          # Service type (smtp, api, local, webhook)
                    }
                },
                "total_services": int,
                "configured_services": int,
                "connected_services": int
            }

        Examples:
            # Check all services
            email_status()
            # Returns status for all configured services

            # Check specific service
            email_status(service="sendgrid")
            # Returns status only for SendGrid service

        Notes:
            - Tests actual connectivity, not just configuration presence
            - Connection tests are quick (timeout after 5-10 seconds)
            - API keys and passwords are not exposed in results
        """
        services_to_check = [service] if service else list(server.services.keys())
        service_statuses = {}

        for svc_name in services_to_check:
            if svc_name in server.services:
                email_service = server.services[svc_name]
                status = await email_service.test_connection()
                service_statuses[svc_name] = {
                    "configured": True,
                    "connected": status.get(
                        "connected",
                        status.get("smtp_connected", False) or status.get("imap_connected", False),
                    ),
                    "error": status.get("error") or status.get("smtp_error") or status.get("imap_error"),
                    "type": email_service.config.type,
                }
            else:
                service_statuses[svc_name] = {
                    "configured": False,
                    "connected": False,
                    "error": f"Service '{svc_name}' not configured",
                    "type": "unknown",
                }

        configured_count = sum(1 for s in service_statuses.values() if s["configured"])
        connected_count = sum(1 for s in service_statuses.values() if s["connected"])

        return {
            "server": "Email-MCP",
            "version": "0.4.0",
            "services": service_statuses,
            "total_services": len(service_statuses),
            "configured_services": configured_count,
            "connected_services": connected_count,
            "tools_exposed": 32,
            "tools": [
                "send_email",
                "check_inbox",
                "fetch_email_detail",
                "search_emails",
                "delete_email",
                "mark_email_read",
                "mark_email_unread",
                "list_folders",
                "create_folder",
                "delete_folder",
                "rename_folder",
                "email_status",
                "configure_service",
                "remove_service",
                "list_services",
                "email_help",
                "mailing_lists_catalog",
                "mailing_list_latest",
                "suggest_email_subject",
                "email_agentic_assist",
                "start_watcher",
                "stop_watcher",
                "watcher_status",
                "add_contact",
                "search_contacts",
                "run_workflow",
                "add_auto_rule",
                "list_auto_rules",
                "delete_auto_rule",
                "list_pending_replies",
                "approve_reply",
                "auto_respond_now",
            ],
            "message": f"Email MCP server v0.4.1 - {connected_count}/{len(service_statuses)} services connected",
        }

    @mcp.tool()
    async def configure_service(
        name: str,
        type: str,
        config: dict[str, Any],
        enabled: bool = True,
    ) -> dict[str, Any]:
        """Configure a new email service dynamically.

        Adds a new email service configuration at runtime. The service will be
        available for sending emails and inbox checking immediately.

        Args:
            name: Unique name for the service (e.g., "my-sendgrid", "dev-mailhog")
            type: Service type - "smtp", "api", "local", or "webhook"
            config: Service-specific configuration dictionary
            enabled: Whether the service should be enabled (default: True)

        Returns:
            Dictionary with configuration result:
            {
                "success": bool,
                "service": str,       # Service name
                "type": str,          # Service type
                "message": str        # Success/error message
            }

        Examples:
            # Configure SendGrid API service
            configure_service(
                name="my-sendgrid",
                type="api",
                config={
                    "api_key": "your-sendgrid-key",
                    "api_url": "https://api.sendgrid.com/v3/mail/send",
                    "from_email": "noreply@yourdomain.com",
                    "service_type": "sendgrid"
                }
            )

            # Configure local MailHog for testing
            configure_service(
                name="local-testing",
                type="local",
                config={
                    "smtp_server": "localhost",
                    "smtp_port": 1025,
                    "http_url": "http://localhost:8025",
                    "service_type": "mailhog"
                }
            )

        Notes:
            - Service names must be unique
            - Configuration is stored in memory (not persisted)
            - Use list_services() to see available services
        """
        if name in server.services:
            return {
                "success": False,
                "service": name,
                "message": f"Service '{name}' already exists",
            }

        try:
            service_config = EmailServiceConfig(name=name, type=type, enabled=enabled, config=config)
            server.services[name] = EmailServiceFactory.create_service(service_config)

            logger.info("Service configured", service=name, type=type)
            return {
                "success": True,
                "service": name,
                "type": type,
                "message": f"Successfully configured {type} service '{name}' - ready for use",
            }
        except Exception as e:
            logger.error("Failed to configure service", service=name, error=str(e))
            return {
                "success": False,
                "service": name,
                "message": f"Configuration failed for service '{name}': {e!s}",
            }

    @mcp.tool()
    async def list_services() -> dict[str, Any]:
        """List all configured email services.

        Returns information about all available email services, their types,
        and configuration status.

        Returns:
            Dictionary with service information:
            {
                "services": {
                    "service_name": {
                        "type": str,        # Service type
                        "enabled": bool,    # Whether service is enabled
                        "configured": bool, # Whether properly configured
                        "description": str  # Human-readable description
                    }
                },
                "count": int,           # Total number of services
                "enabled_count": int,   # Number of enabled services
                "types": [str]          # List of available service types
            }

        Examples:
            # List all services
            list_services()
            # Returns: {
            #     "services": {
            #         "default": {"type": "smtp", "enabled": true, "configured": true, "description": "Default SMTP/IMAP service"},
            #         "sendgrid": {"type": "api", "enabled": true, "configured": true, "description": "SendGrid transactional email"}
            #     },
            #     "count": 2,
            #     "enabled_count": 2,
            #     "types": ["smtp", "api", "local", "webhook"]
            # }

        Notes:
            - Shows both automatically configured and manually added services
            - Configuration status indicates if required credentials are available
            - Use email_status() to test actual connectivity
        """
        service_info = {}
        enabled_count = 0

        for name, service in server.services.items():
            configured = True
            description = f"{service.__class__.__name__.replace('EmailService', '').lower()} service"

            # Check if service is properly configured
            if isinstance(service, SMTPEmailService):
                configured = bool(service.smtp_server and service.smtp_user and service.smtp_password)
                description = "SMTP/IMAP email service"
            elif isinstance(service, APIEmailService):
                configured = bool(service.api_key and service.api_url and service.from_email)
                description = f"{service.service_type.title()} transactional email API"
            elif isinstance(service, LocalEmailService):
                configured = bool(service.smtp_server)
                description = f"Local {service.service_type} testing service"
            elif isinstance(service, WebhookEmailService):
                configured = bool(service.webhook_url)
                description = f"{service.service_type.title()} webhook integration"

            service_info[name] = {
                "type": service.config.type,
                "enabled": service.config.enabled,
                "configured": configured,
                "description": description,
            }

            if service.config.enabled:
                enabled_count += 1

        return {
            "services": service_info,
            "count": len(service_info),
            "enabled_count": enabled_count,
            "types": ["smtp", "api", "local", "webhook"],
        }

    @mcp.tool()
    async def email_help() -> dict[str, Any]:
        """Get help and usage information for email MCP tools and services.

        Returns comprehensive help information including available tools, supported services,
        usage examples, configuration requirements, and common use cases.

        Returns:
            Dictionary with service and tool information:
            {
                "server": str,              # Server name
                "version": str,             # Server version
                "description": str,         # Server description
                "supported_services": {     # Available service types
                    "smtp": str,            # Description of SMTP services
                    "api": str,             # Description of API services
                    "local": str,           # Description of local services
                    "webhook": str          # Description of webhook services
                },
                "tools": [...],             # List of available tools
                "examples": [...],          # Usage examples
                "notes": [...]              # Important notes and tips
            }

        Examples:
            # Get comprehensive help
            email_help()
            # Returns full documentation for all services and tools

        Notes:
            - Use list_services() to see currently configured services
            - Use email_status() to test service connectivity
            - Use configure_service() to add new services dynamically
        """
        return {
            "server": "Email-MCP",
            "version": "0.4.1",
            "description": "Multi-service email platform supporting SMTP, APIs, local testing, webhooks, search, and AI features",
            "supported_services": {
                "smtp": "Standard email providers (Gmail, Outlook, Yahoo, iCloud, ProtonMail)",
                "api": "Transactional email APIs (SendGrid, Mailgun, Postmark, Amazon SES, Resend)",
                "local": "Local testing services (MailHog, Mailpit, MailCatcher, Inbucket)",
                "webhook": "Chat/webhook integrations (Slack, Discord, Telegram, GitHub)",
            },
            "tools": [
                {
                    "name": "send_email",
                    "description": "Send emails via any configured service",
                    "usage": 'send_email(to="user@example.com", subject="Hello", body="Message", service="sendgrid")',
                },
                {
                    "name": "check_inbox",
                    "description": "Check inbox via IMAP or service APIs",
                    "usage": 'check_inbox(service="default", folder="INBOX", limit=10)',
                },
                {
                    "name": "fetch_email_detail",
                    "description": "Get full email with text and HTML body",
                    "usage": 'fetch_email_detail(email_id="12345", service="default")',
                },
                {
                    "name": "search_emails",
                    "description": "Full-text IMAP search on subject and body",
                    "usage": 'search_emails(query="invoice", folder="INBOX")',
                },
                {
                    "name": "delete_email",
                    "description": "Delete/move-to-trash a single email",
                    "usage": 'delete_email(email_id="12345")',
                },
                {
                    "name": "mark_email_read",
                    "description": "Mark a single email as read (SEEN flag)",
                    "usage": 'mark_email_read(email_id="12345")',
                },
                {
                    "name": "mailing_lists_catalog",
                    "description": "List EMAIL_MCP_MAILING_LISTS presets (named folders/filters)",
                    "usage": "mailing_lists_catalog()",
                },
                {
                    "name": "mailing_list_latest",
                    "description": "Newest messages for a named list preset (newsletters)",
                    "usage": 'mailing_list_latest(list_id="alphasignal")',
                },
                {
                    "name": "email_status",
                    "description": "Test connectivity for services",
                    "usage": "email_status(service='sendgrid')",
                },
                {
                    "name": "configure_service",
                    "description": "Add new email services dynamically",
                    "usage": "configure_service(name='my-api', type='api', config={...})",
                },
                {
                    "name": "remove_service",
                    "description": "Remove a runtime configured service",
                    "usage": 'remove_service(name="gmail")',
                },
                {
                    "name": "list_services",
                    "description": "List all configured email services",
                    "usage": "list_services()",
                },
                {
                    "name": "email_help",
                    "description": "Get this help information",
                    "usage": "email_help()",
                },
                {
                    "name": "suggest_email_subject",
                    "description": "Suggest subject lines via MCP sampling",
                    "usage": 'suggest_email_subject(body="...")',
                },
                {
                    "name": "email_agentic_assist",
                    "description": "Multi-step email plan via sampling",
                    "usage": 'email_agentic_assist(goal="...")',
                },
            ],
            "configuration": {
                "environment_variables": {
                    "SMTP_SERVER": "SMTP server hostname (e.g., smtp.gmail.com)",
                    "SMTP_USER": "SMTP username/email",
                    "SMTP_PASSWORD": "SMTP password or app password",
                    "IMAP_SERVER": "IMAP server hostname (e.g., imap.gmail.com)",
                    "IMAP_USER": "IMAP username/email",
                    "IMAP_PASSWORD": "IMAP password",
                    "EMAIL_MCP_MAILING_LISTS": "JSON array of {id, service, folder, limit, unread_only, from_contains?, subject_contains?}",
                    "EMAIL_MCP_MAILING_LISTS_FILE": "Optional path to JSON file (same schema as EMAIL_MCP_MAILING_LISTS)",
                    "SENDGRID_API_KEY": "SendGrid API key",
                    "MAILGUN_API_KEY": "Mailgun API key",
                    "RESEND_API_KEY": "Resend API key",
                    "MAILHOG_ENABLED": "Set to 'true' to enable MailHog",
                    "SLACK_WEBHOOK_URL": "Slack webhook URL for notifications",
                },
                "dynamic_configuration": "Use configure_service() to add services at runtime",
            },
            "examples": [
                "# Send via different services",
                'send_email(to="user@example.com", subject="Hello", body="Test", service="default")',
                'send_email(to="user@example.com", subject="Welcome", body="Welcome!", service="sendgrid")',
                'send_email(to="#general", subject="Alert", body="System alert", service="slack")',
                "",
                "# Check inboxes",
                'check_inbox(service="default", unread_only=True)',
                'check_inbox(service="mailhog", limit=20)',
                "",
                "# Mailing lists (newsletters)",
                "mailing_lists_catalog()",
                'mailing_list_latest(list_id="alphasignal")',
                "",
                "# Configure new services",
                "configure_service(name='my-mailgun', type='api', config={'api_key': 'key', 'api_url': 'url', 'from_email': 'me@domain.com', 'service_type': 'mailgun'})",
                "",
                "# Service management",
                "list_services()",
                "email_status()",
            ],
            "notes": [
                "Gmail requires App Passwords, not regular passwords",
                "Enable 2-Step Verification to generate Gmail App Passwords",
                "API services may have rate limits and sending limits",
                "Local testing services don't send real emails",
                "Webhook services convert emails to chat messages",
                "IMAP services support standard folder names (INBOX, Sent, etc.)",
                "All operations are performed asynchronously",
                "Service configurations are stored in memory (not persisted across restarts)",
            ],
        }

    @mcp.tool()
    async def fetch_email_detail(
        email_id: str,
        service: str = "default",
        folder: str = "INBOX",
    ) -> dict[str, Any]:
        """Fetch a single email by ID with full body (text + HTML).

        Returns the complete email including decoded text body, HTML body,
        and all headers. Requires IMAP access on the target service.

        ## Return Format
        {success, id, subject, from, to, cc, date, text_body, html_body, headers, service}
        """
        if service not in server.services:
            return {"success": False, "error": f"Service {service!r} not available"}
        result = await server.services[service].fetch_message(folder, email_id)
        if result.get("success"):
            result["message"] = f"Fetched email {email_id[:20]}... from {folder}"
            result = wrap_untrusted_dict(result, source="email_detail")
        else:
            result["message"] = f"Failed to fetch email: {result.get('error')}"
        return result

    @mcp.tool()
    async def delete_email(
        email_id: str,
        service: str = "default",
        folder: str = "INBOX",
    ) -> dict[str, Any]:
        """Delete a single email by ID (moves to Trash via IMAP).

        ## Return Format
        {success, service, email_id, message}
        """
        if service not in server.services:
            return {"success": False, "error": f"Service {service!r} not available"}
        return await server.services[service].delete_message(folder, email_id)

    @mcp.tool()
    async def move_email(
        email_id: str,
        to_folder: str,
        service: str = "default",
        folder: str = "INBOX",
    ) -> dict[str, Any]:
        """Move an email between IMAP folders (COPY + DELETE).

        ## Return Format
        {success, service, email_id, message}
        """
        if service not in server.services:
            return {"success": False, "error": f"Service {service!r} not available"}
        return await server.services[service].move_message(folder, to_folder, email_id)

    @mcp.tool()
    async def flag_spam(
        email_id: str,
        service: str = "default",
        folder: str = "INBOX",
    ) -> dict[str, Any]:
        """Flag an email as spam (Junk flag + move to Spam folder).

        ## Return Format
        {success, service, email_id, message}
        """
        if service not in server.services:
            return {"success": False, "error": f"Service {service!r} not available"}
        return await server.services[service].flag_spam(folder, email_id)

    @mcp.tool()
    async def mark_email_read(
        email_id: str,
        service: str = "default",
        folder: str = "INBOX",
    ) -> dict[str, Any]:
        """Mark a single email as read (SEEN flag) via IMAP.

        ## Return Format
        {success, service, email_id, message}
        """
        if service not in server.services:
            return {"success": False, "error": f"Service {service!r} not available"}
        return await server.services[service].mark_read(folder, email_id)

    @mcp.tool()
    async def mark_email_unread(
        email_id: str,
        service: str = "default",
        folder: str = "INBOX",
    ) -> dict[str, Any]:
        """Mark a single email as unread (remove SEEN flag) via IMAP.

        ## Return Format
        {success, service, email_id, message}
        """
        if service not in server.services:
            return {"success": False, "error": f"Service {service!r} not available"}
        return await server.services[service].mark_unread(folder, email_id)

    @mcp.tool()
    async def list_folders(
        service: str = "default",
    ) -> dict[str, Any]:
        """List all IMAP folders/mailboxes for a service.

        ## Return Format
        {success, folders: [{name, delimiter}], service}
        """
        if service not in server.services:
            return {"success": False, "error": f"Service {service!r} not available"}
        svc = server.services[service]
        folders = await svc.list_folders(service)
        return {"success": True, "folders": folders, "service": service, "count": len(folders)}

    @mcp.tool()
    async def create_folder(
        folder: str,
        service: str = "default",
    ) -> dict[str, Any]:
        """Create a new IMAP folder.

        ## Return Format
        {success, folder, message}
        """
        if service not in server.services:
            return {"success": False, "error": f"Service {service!r} not available"}
        return await server.services[service].create_folder(folder)

    @mcp.tool()
    async def delete_folder(
        folder: str,
        service: str = "default",
    ) -> dict[str, Any]:
        """Delete an IMAP folder.

        ## Return Format
        {success, folder, message}
        """
        if service not in server.services:
            return {"success": False, "error": f"Service {service!r} not available"}
        return await server.services[service].delete_folder(folder)

    @mcp.tool()
    async def rename_folder(
        old_name: str,
        new_name: str,
        service: str = "default",
    ) -> dict[str, Any]:
        """Rename an IMAP folder.

        ## Return Format
        {success, old_name, new_name, message}
        """
        if service not in server.services:
            return {"success": False, "error": f"Service {service!r} not available"}
        return await server.services[service].rename_folder(old_name, new_name)

    @mcp.tool()
    async def search_emails(
        query: str,
        service: str = "default",
        folder: str = "INBOX",
        limit: int = 20,
    ) -> dict[str, Any]:
        """Search emails via IMAP SEARCH command (subject/from/body keywords).

        Uses IMAP SEARCH to find messages matching the query string,
        then fetches headers for the most recent matches.

        ## Return Format
        {success, emails: [{id, subject, from, date}], count, service, folder, query}
        """
        if service not in server.services:
            return {"success": False, "error": f"Service {service!r} not available"}

        svc = server.services[service]
        if not isinstance(svc, SMTPEmailService) or not svc.imap_server:
            # Fallback: use check_inbox with subject/filter
            return await svc.check_inbox(
                folder=folder,
                limit=limit,
                unread_only=False,
                subject_contains=query,
                from_contains=None,
            )

        try:

            def search_sync():
                mail = imaplib.IMAP4_SSL(svc.imap_server, svc.imap_port)
                mail.login(svc.imap_user, svc.imap_password)
                mail.select(folder)

                # IMAP SEARCH: look in subject and body
                search_key = f'(OR SUBJECT "{query}" BODY "{query}")'
                _status, messages = mail.search(None, search_key)
                email_ids_ = messages[0].split() if messages and messages[0] else []
                if not email_ids_:
                    mail.close()
                    mail.logout()
                    return []

                email_ids_ = list(reversed(email_ids_))[:limit]
                emails_ = []
                for eid in email_ids_:
                    st, md = mail.fetch(eid, "(RFC822.HEADER)")
                    if st != "OK":
                        continue
                    em = email.message_from_bytes(md[0][1])
                    emails_.append(
                        {
                            "id": eid.decode(),
                            "subject": sanitize_text(decode_email_header(em.get("Subject", ""))) or "(No Subject)",
                            "from": sanitize_text(decode_email_header(em.get("From", ""))) or "Unknown",
                            "date": sanitize_text(decode_email_header(em.get("Date", ""))) or "Unknown",
                        }
                    )
                mail.close()
                mail.logout()
                return emails_

            loop = asyncio.get_event_loop()
            emails = await loop.run_in_executor(None, search_sync)
            wrapped = wrap_untrusted_list(emails, source="search")
            return {
                "success": True,
                "emails": wrapped,
                "count": len(wrapped),
                "service": service,
                "folder": folder,
                "query": query,
                "message": f"Found {len(wrapped)} results for '{query}' in {folder}",
            }
        except Exception as e:
            return {"success": False, "error": f"Search failed: {e!s}"}

    @mcp.tool()
    async def remove_service(name: str) -> dict[str, Any]:
        """Remove a dynamically configured email service.

        ## Return Format
        {success, service, message}
        """
        if name not in server.services:
            return {"success": False, "service": name, "message": f"Service {name!r} not found"}
        if name == "default":
            return {"success": False, "service": name, "message": "Cannot remove the 'default' service"}
        del server.services[name]
        logger.info("Service removed", service=name)
        return {"success": True, "service": name, "message": f"Service {name!r} removed"}

    @mcp.tool()
    async def start_watcher(
        interval: int = 60,
        webhook_url: str = "",
        services: str = '[{"name":"default","folder":"INBOX"}]',
    ) -> dict[str, Any]:
        """Start background IMAP polling for new emails.

        Polls configured services at intervals. When new unread emails arrive,
        POSTs a JSON payload to the webhook URL. Designed for integration with
        robofang (TTS alerts) or fleet-agent (workflow triggers).

        ## Return Format
        {running, message, services: [name]}

        ## Examples
        start_watcher(interval=60, webhook_url="http://localhost:10956/api/alerts")
        """
        import json as _j

        svc_list = _j.loads(services) if isinstance(services, str) else services
        # Ensure each entry has at least name and folder
        svc_list = [
            {"name": s.get("name", "default"), "folder": s.get("folder", "INBOX")}
            if isinstance(s, dict)
            else {"name": str(s), "folder": "INBOX"}
            for s in svc_list
        ]
        from .watcher import start_watcher as _sw

        return _sw(interval, webhook_url, svc_list, server.mcp)

    @mcp.tool()
    async def stop_watcher() -> dict[str, Any]:
        """Stop the background mail watcher.

        ## Return Format
        {running, message}
        """
        from .watcher import stop_watcher as _sw

        return _sw()

    @mcp.tool()
    async def watcher_status() -> dict[str, Any]:
        """Check if the mail watcher is running.

        ## Return Format
        {running, config: {interval, webhook_url, services}}
        """
        from .watcher import watcher_status as _ws

        return _ws()

    @mcp.tool()
    async def add_contact(
        name: str = "",
        email: str = "",
        phone: str = "",
        notes: str = "",
        group: str = "",
    ) -> dict[str, Any]:
        """Add a contact to the address book.

        ## Return Format
        {success, contact: {id, name, email, phone, notes, group}}
        """
        from .contacts import add_contact as _ac

        return _ac(name, email, phone, notes, group)

    @mcp.tool()
    async def search_contacts(query: str) -> dict[str, Any]:
        """Search contacts by name or email.

        ## Return Format
        {contacts: [{id, name, email, phone, group}]}
        """
        from .contacts import search_contacts as _sc

        return {"contacts": _sc(query)}

    @mcp.tool()
    async def run_workflow(
        workflow: str = "love-letter",
        recipient: str = "beloved",
        tone: str = "sincere",
        mood: str = "warm",
        format: str = "text",
    ) -> dict[str, Any]:
        """Generate a creative email using a preset workflow.

        Supported workflows: love-letter, breakup, thank-you, complaint,
        apology, fan-mail, hate-mail. Recipients can be anything: person,
        pet, object, or concept. Formats: text, ascii, svg.

        ## Return Format
        {success, workflow, response (the generated text), format}

        ## Examples
        run_workflow(workflow="love-letter", recipient="Landlady", format="ascii")
        run_workflow(workflow="complaint", recipient="The WiFi Router", tone="comedic")
        """
        from .workflows import FORMAT_INSTRUCTIONS as _FMT
        from .workflows import WORKFLOW_TEMPLATES as _TMPL

        if workflow not in _TMPL:
            return {"success": False, "error": f"Unknown workflow '{workflow}'"}
        query = _TMPL[workflow].format(
            recipient=recipient, tone=tone, mood=mood, fmt_text=_FMT.get(format, _FMT["text"])
        )
        from .ai import AIRouter

        _router = AIRouter(server.mcp)
        response = await _router.route_query(query)
        return {"success": True, "workflow": workflow, "response": response, "format": format}

    @mcp.tool()
    async def add_auto_rule(
        name: str,
        match_pattern: str,
        reply_body: str = "",
        reply_subject: str = "",
        match_field: str = "subject",
        use_ai: bool = False,
        auto_send: bool = False,
        ai_prompt: str = "",
        service: str = "default",
    ) -> dict[str, Any]:
        """Add an auto-respond rule.

        When incoming mail matches the pattern, the rule fires.
        use_ai=true generates a reply via LLM. auto_send sends it immediately
        without human approval. Otherwise the reply goes to the pending queue.

        ## Return Format
        {success, rule: {id, name, match_pattern, ...}}

        ## Examples
        add_auto_rule(name="Invoice reply", match_pattern="invoice", reply_body="Thanks, we'll process this.")
        add_auto_rule(name="AI reply", match_pattern="urgent", use_ai=True, ai_prompt="Reply politely saying I'm away", auto_send=False)
        """
        from .autorespond import add_rule as _ar

        return _ar(
            name, match_field, match_pattern, reply_body, reply_subject, use_ai, auto_send, ai_prompt, service
        )

    @mcp.tool()
    async def list_auto_rules() -> dict[str, Any]:
        """List all auto-respond rules.

        ## Return Format
        {rules: [{id, name, match_pattern, reply_body, use_ai, auto_send, enabled}]}
        """
        from .autorespond import list_rules as _lr

        return {"rules": _lr()}

    @mcp.tool()
    async def delete_auto_rule(rule_id: str) -> dict[str, Any]:
        """Delete an auto-respond rule by ID.

        ## Return Format
        {success, message}
        """
        from .autorespond import delete_rule as _dr

        return _dr(rule_id)

    @mcp.tool()
    async def list_pending_replies() -> dict[str, Any]:
        """List pending auto-replies awaiting human approval.

        ## Return Format
        {pending: [{id, email_subject, email_from, reply_body, status}]}
        """
        from .autorespond import list_pending as _lp

        return {"pending": _lp()}

    @mcp.tool()
    async def approve_reply(pending_id: str) -> dict[str, Any]:
        """Approve a pending auto-reply and send it immediately.

        ## Return Format
        {success, message, sent}
        """
        from .autorespond import approve_pending as _ap

        result = _ap(pending_id)
        if not result.get("success"):
            return result

        pend = result["pending"]
        svc = pend.get("service", "default")
        if svc not in server.services:
            return {**result, "sent": False, "send_message": f"Service {svc!r} not available"}

        send_result = await server.services[svc].send_email(
            to=pend.get("email_from", ""),
            subject=pend.get("reply_subject", ""),
            body=pend.get("reply_body", ""),
        )
        result["sent"] = send_result.get("success", False)
        result["send_message"] = (
            "Reply sent" if send_result.get("success") else send_result.get("error", "Send failed")
        )
        return result

    @mcp.tool()
    async def auto_respond_now(
        email_id: str,
        service: str = "default",
        folder: str = "INBOX",
    ) -> dict[str, Any]:
        """Manually trigger AI auto-respond on a specific email.

        Fetches the email, generates an AI reply, and adds it to the
        pending queue for approval.

        ## Return Format
        {success, matched, rule?: name, queued, reply_subject?}
        """
        result = await server.services[service].fetch_message(folder, email_id)
        if not result.get("success"):
            return {"success": False, "error": f"Email {email_id} not found"}
        from .autorespond import add_pending, match_rule

        rule = match_rule(result)
        if not rule:
            return {"success": True, "matched": False, "message": "No rule matched"}
        from .ai import AIRouter

        _router = AIRouter(server.mcp)
        prompt = (
            rule.get("ai_prompt", "")
            or f"Write a friendly reply to this email.\n\nFrom: {result.get('from', '')}\nSubject: {result.get('subject', '')}\nBody: {result.get('text_body', '')[:2000]}"
        )
        reply_body = await _router.route_query(prompt)
        reply_subject = f"Re: {result.get('subject', '')}"
        add_pending(result, reply_body, reply_subject, rule["id"], service)
        return {
            "success": True,
            "matched": True,
            "rule": rule["name"],
            "queued": True,
            "reply_subject": reply_subject,
        }
