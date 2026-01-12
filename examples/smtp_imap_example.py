#!/usr/bin/env python3
"""
SMTP/IMAP Email Service Example

This example demonstrates how to use standard SMTP/IMAP email services
with the Email MCP server.

Supported providers: Gmail, Outlook, Yahoo, iCloud, ProtonMail, etc.
"""

import asyncio


async def main():
    """Demonstrate SMTP/IMAP email operations."""

    print("🔄 SMTP/IMAP Email Service Examples")
    print("=" * 50)

    # 1. Send a basic email via SMTP
    print("\n📧 1. Sending basic email via SMTP...")
    try:
        result = await send_email(
            to="recipient@example.com",
            subject="Test Email",
            body="Hello from Email MCP SMTP service!"
        )
        print(f"✅ Email sent: {result['success']}")
    except Exception as e:
        print(f"❌ SMTP send failed: {e}")

    # 2. Send HTML email with attachments
    print("\n🎨 2. Sending HTML email...")
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
        print(f"✅ HTML email sent: {result['success']}")
    except Exception as e:
        print(f"❌ HTML send failed: {e}")

    # 3. Check inbox via IMAP
    print("\n📬 3. Checking inbox via IMAP...")
    try:
        result = await check_inbox(limit=5, unread_only=True)
        print(f"📨 Found {result['count']} unread emails")
        for email in result['emails'][:3]:  # Show first 3
            print(f"   • {email['subject']} - {email['from']}")
    except Exception as e:
        print(f"❌ IMAP check failed: {e}")

    # 4. Check different folder
    print("\n📁 4. Checking Sent folder...")
    try:
        result = await check_inbox(folder="Sent", limit=3)
        print(f"📤 Found {result['count']} sent emails")
    except Exception as e:
        print(f"❌ Sent folder check failed: {e}")

    print("\n✅ SMTP/IMAP examples completed!")


if __name__ == "__main__":
    # Note: These functions would be available through MCP
    # In a real scenario, you'd call them via the MCP protocol
    print("This example shows how to use SMTP/IMAP services.")
    print("In practice, these functions are called through the MCP server.")
    print("\nExample MCP calls:")
    print("- send_email(to='user@example.com', subject='Hello', body='Message')")
    print("- check_inbox(limit=10, unread_only=True)")
    print("- email_status()")
