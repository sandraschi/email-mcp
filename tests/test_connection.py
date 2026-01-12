"""Quick test script for email connection."""

import asyncio
import smtplib
import imaplib
import sys

# Hotmail/Outlook settings
SMTP_SERVER = "smtp.office365.com"
SMTP_PORT = 587
IMAP_SERVER = "outlook.office365.com"
IMAP_PORT = 993
EMAIL = "sandraschipal@hotmail.com"
PASSWORD = "Lara51511175mi"

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

