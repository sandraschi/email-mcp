#!/usr/bin/env python3
"""
Transactional Email API Services Example

This example demonstrates how to use transactional email APIs
with the Email MCP server.

Supported services: SendGrid, Mailgun, Resend, Amazon SES, Postmark
"""

import asyncio
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


async def main():
    """Demonstrate transactional email API operations."""

    logger.info("Transactional Email API Examples")
    logger.info("=" * 50)

    # 1. Send email via SendGrid
    logger.info("1. Sending via SendGrid...")
    try:
        result = await send_email(
            to="customer@example.com",
            subject="Welcome to Our Service",
            body="Thank you for signing up!",
            html="""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h1 style="color: #333;">Welcome!</h1>
                <p>Thank you for joining our service. We're excited to have you!</p>
                <div style="background: #f5f5f5; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3>Your account is ready</h3>
                    <p>You can now access all features of our platform.</p>
                </div>
                <a href="#" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Get Started</a>
            </div>
            """,
            service="sendgrid"
        )
        logger.info(f"SendGrid email sent: {result['success']}")
    except Exception as e:
        logger.error(f"SendGrid send failed: {e}")

    # 2. Send bulk email via Mailgun
    logger.info("2. Sending bulk email via Mailgun...")
    try:
        result = await send_email(
            to=["user1@example.com", "user2@example.com", "user3@example.com"],
            subject="Monthly Newsletter",
            body="Check out our latest updates!",
            html="<h1>Monthly Newsletter</h1><p>Check out our latest updates...</p>",
            service="mailgun"
        )
        logger.info(f"Mailgun bulk email sent: {result['success']}")
    except Exception as e:
        logger.error(f"Mailgun send failed: {e}")

    # 3. Send transactional email via Resend
    logger.info("3. Sending transactional email via Resend...")
    try:
        result = await send_email(
            to="user@example.com",
            subject="Password Reset",
            body="Click the link below to reset your password",
            html="""
            <div style="font-family: monospace; background: #000; color: #00ff00; padding: 20px;">
                <h2>PASSWORD RESET</h2>
                <p>Click the link below to reset your password:</p>
                <a href="#" style="color: #00ff00; text-decoration: underline;">Reset Password</a>
                <p>This link expires in 24 hours.</p>
            </div>
            """,
            service="resend"
        )
        logger.info(f"Resend transactional email sent: {result['success']}")
    except Exception as e:
        logger.error(f"Resend send failed: {e}")

    # 4. Check service status
    logger.info("4. Checking service status...")
    try:
        status = await email_status()
        logger.info(f"Services configured: {status['configured_services']}")
        logger.info(f"Services connected: {status['connected_services']}")

        for svc_name, svc_status in status['services'].items():
            if svc_status['configured']:
                status_text = "connected" if svc_status['connected'] else "disconnected"
                logger.info(f"  - {svc_name}: {status_text}")
    except Exception as e:
        logger.error(f"Status check failed: {e}")

    logger.info("API service examples completed!")


if __name__ == "__main__":
    logger.info("This example shows how to use transactional email APIs.")
    logger.info("In practice, these functions are called through the MCP server.")
    logger.info("Example MCP calls:")
    logger.info("- send_email(to='user@example.com', subject='Welcome', body='Hi!', service='sendgrid')")
    logger.info("- email_status()")
    logger.info("- list_services()")
