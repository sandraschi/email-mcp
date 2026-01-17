#!/usr/bin/env python3
"""
Local Testing and Webhook Services Example

This example demonstrates how to use local testing services and webhooks
with the Email MCP server.

Local services: MailHog, Mailpit, MailCatcher, Inbucket
Webhook services: Slack, Discord, Telegram, GitHub
"""

import asyncio
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


async def main():
    """Demonstrate local testing and webhook operations."""

    logger.info("Local Testing & Webhook Examples")
    logger.info("=" * 50)

    # 1. Send test email to MailHog
    logger.info("1. Sending test email to MailHog...")
    try:
        result = await send_email(
            to="test@localhost",
            subject="Test Email",
            body="This is a test email for development.",
            html="<h1>Test Email</h1><p>This is a test for the MailHog web UI.</p>",
            service="mailhog"
        )
        logger.info(f"MailHog email sent: {result['success']}")
        if result['success']:
            logger.info("Check http://localhost:8025 for the email in web UI")
    except Exception as e:
        logger.error(f"MailHog send failed: {e}")

    # 2. Check MailHog inbox
    logger.info("2. Checking MailHog inbox...")
    try:
        result = await check_inbox(service="mailhog", limit=10)
        logger.info(f"Found {result['count']} emails in MailHog")
        for email in result['emails'][:3]:  # Show first 3
            logger.info(f"  - {email['subject']} - {email['from']} ({email['date']})")
    except Exception as e:
        logger.error(f"MailHog inbox check failed: {e}")

    # 3. Send notification to Slack
    logger.info("3. Sending notification to Slack...")
    try:
        result = await send_email(
            to="#dev-alerts",
            subject="🚨 System Alert",
            body="High CPU usage detected on production server.",
            html="""
            <div style="border-left: 4px solid #ff6b6b; padding-left: 16px; margin: 16px 0;">
                <h3 style="color: #ff6b6b; margin: 0;">🚨 System Alert</h3>
                <p style="margin: 8px 0;"><strong>High CPU usage detected</strong></p>
                <p style="margin: 8px 0;">Server: prod-web-01<br>CPU: 95%<br>Time: {timestamp}</p>
                <p style="margin: 8px 0; color: #666;">This is an automated alert from the monitoring system.</p>
            </div>
            """,
            service="slack"
        )
        logger.info(f"Slack notification sent: {result['success']}")
    except Exception as e:
        logger.error(f"Slack send failed: {e}")

    # 4. Send alert to Discord
    logger.info("4. Sending alert to Discord...")
    try:
        result = await send_email(
            to="#alerts",
            subject="🔥 Database Backup Failed",
            body="Database backup job failed on server db-01.",
            service="discord"
        )
        logger.info(f"Discord alert sent: {result['success']}")
    except Exception as e:
        logger.error(f"Discord send failed: {e}")

    # 5. Send to Telegram (if configured)
    logger.info("5. Sending message to Telegram...")
    try:
        result = await send_email(
            to="@mybot",
            subject="New User Registration",
            body="User john.doe@example.com just registered.",
            service="telegram"
        )
        logger.info(f"Telegram message sent: {result['success']}")
    except Exception as e:
        logger.error(f"Telegram send failed: {e}")

    # 6. Dynamic service configuration
    logger.info("6. Configuring new service dynamically...")
    try:
        result = await configure_service(
            name="my-custom-mailgun",
            type="api",
            config={
                "api_key": "my-mailgun-api-key",
                "api_url": "https://api.mailgun.net/v3/mydomain.com/messages",
                "from_email": "noreply@mydomain.com",
                "service_type": "mailgun"
            }
        )
        logger.info(f"Service configured: {result['success']}")
        if result['success']:
            logger.info("New service 'my-custom-mailgun' is now available")
    except Exception as e:
        logger.error(f"Service configuration failed: {e}")

    # 7. List all services
    logger.info("7. Listing all configured services...")
    try:
        services = await list_services()
        logger.info(f"Total services: {services['count']}")
        logger.info(f"Enabled services: {services['enabled_count']}")

        for name, info in services['services'].items():
            status = "configured and enabled" if info['configured'] and info['enabled'] else "not fully configured"
            logger.info(f"  - {name}: {info['description']} ({status})")
    except Exception as e:
        logger.error(f"Service listing failed: {e}")

    logger.info("Local testing & webhook examples completed!")


if __name__ == "__main__":
    logger.info("This example shows how to use local testing and webhook services.")
    logger.info("In practice, these functions are called through the MCP server.")
    logger.info("Example MCP calls:")
    logger.info("- send_email(to='test@localhost', subject='Test', body='Hi', service='mailhog')")
    logger.info("- check_inbox(service='mailhog', limit=10)")
    logger.info("- send_email(to='#alerts', subject='Alert', body='Message', service='slack')")
    logger.info("- configure_service(name='my-api', type='api', config={...})")
    logger.info("- list_services()")
