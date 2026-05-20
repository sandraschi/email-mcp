"""Quick test script for email connection.

WARNING: This file is a local debug script, not a proper test.
Credentials should come from environment variables, not hardcoded values.
Use environment vars: SMTP_USER, SMTP_PASSWORD, SMTP_SERVER, IMAP_SERVER
"""

import asyncio
import imaplib
import os
import smtplib
import sys

# Read from environment; no hardcoded defaults
SMTP_SERVER = os.environ.get("SMTP_SERVER", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
IMAP_SERVER = os.environ.get("IMAP_SERVER", "")
IMAP_PORT = int(os.environ.get("IMAP_PORT", "993"))
EMAIL = os.environ.get("SMTP_USER", "")
PASSWORD = os.environ.get("SMTP_PASSWORD", "")


async def test_smtp():
    """Test SMTP connection."""
    print("Testing SMTP connection...")
    try:

        def test():
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
                server.starttls()
                server.login(EMAIL, PASSWORD)
                return True

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, test)
        print("✅ SMTP connection successful!")
        return True
    except Exception as e:
        print(f"❌ SMTP connection failed: {e}")
        return False


async def test_imap():
    """Test IMAP connection."""
    print("Testing IMAP connection...")
    try:

        def test():
            mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT, timeout=10)
            mail.login(EMAIL, PASSWORD)
            mail.logout()
            return True

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, test)
        print("✅ IMAP connection successful!")
        return True
    except Exception as e:
        print(f"❌ IMAP connection failed: {e}")
        return False


async def main():
    """Run tests."""
    print(f"Testing email connection for: {EMAIL}")
    print(f"SMTP Server: {SMTP_SERVER}:{SMTP_PORT}")
    print(f"IMAP Server: {IMAP_SERVER}:{IMAP_PORT}")
    print("-" * 50)

    smtp_ok = await test_smtp()
    print()
    imap_ok = await test_imap()

    print("-" * 50)
    if smtp_ok and imap_ok:
        print("✅ All connections successful!")
        sys.exit(0)
    else:
        print("❌ Some connections failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
