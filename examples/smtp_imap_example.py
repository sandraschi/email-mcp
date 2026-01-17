#!/usr/bin/env python3
"""
SMTP/IMAP Email Service Example

This example demonstrates how to use standard SMTP/IMAP email services
with the Email MCP server.

Supported providers: Gmail, Outlook, Yahoo, iCloud, ProtonMail, etc.
"""

import asyncio
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


async def main():
    """Demonstrate SMTP/IMAP email operations."""

    logger.info("SMTP/IMAP Email Service Examples")
    logger.info("=" * 50)

    # 1. Send a basic email via SMTP
    logger.info("1. Sending basic email via SMTP...")
    try:
        result = await send_email(
            to="recipient@example.com",
            subject="Test Email",
            body="Hello from Email MCP SMTP service!"
        )
        logger.info(f"Email sent: {result['success']}")
    except Exception as e:
        logger.error(f"SMTP send failed: {e}")

    # 2. Send HTML email with CC
    logger.info("2. Sending HTML email...")
    try:
        result = await send_email(
            to="user@example.com",
            subject="Welcome Email",
            body="Please view this in HTML mode",
            html="""
            <h1>Welcome!</h1>
            <p>Thank you for joining our service.</p>
            <ul>
                <li>Feature 1</li>
                <li>Feature 2</li>
                <li>Feature 3</li>
            </ul>
            """,
            cc=["manager@example.com"]
        )
        logger.info(f"HTML email sent: {result['success']}")
    except Exception as e:
        logger.error(f"HTML send failed: {e}")

    # 3. Check inbox via IMAP
    logger.info("3. Checking inbox via IMAP...")
    try:
        result = await check_inbox(limit=5, unread_only=True)
        logger.info(f"Found {result['count']} unread emails")
        for email in result['emails'][:3]:  # Show first 3
            logger.info(f"  - {email['subject']} - {email['from']}")
    except Exception as e:
        logger.error(f"IMAP check failed: {e}")

    # 4. Check different folder
    logger.info("4. Checking Sent folder...")
    try:
        result = await check_inbox(folder="Sent", limit=3)
        logger.info(f"Found {result['count']} sent emails")
    except Exception as e:
        logger.error(f"Sent folder check failed: {e}")

    logger.info("SMTP/IMAP examples completed!")


if __name__ == "__main__":
    # Note: These functions would be available through MCP
    # In a real scenario, you'd call them via the MCP protocol
    logger.info("This example shows how to use SMTP/IMAP services.")
    logger.info("In practice, these functions are called through the MCP server.")
    logger.info("Example MCP calls:")
    logger.info("- send_email(to='user@example.com', subject='Hello', body='Message')")
    logger.info("- check_inbox(limit=10, unread_only=True)")
    logger.info("- email_status()")
