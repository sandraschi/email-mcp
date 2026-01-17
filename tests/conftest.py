"""Pytest configuration for minimail-mcp tests."""

import pytest
import sys
import os
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Test fixtures for email testing
@pytest.fixture
def mock_smtp_server():
    """Mock SMTP server for testing."""
    # This would be implemented with aiosmtpd or similar
    return None

@pytest.fixture
def mock_imap_server():
    """Mock IMAP server for testing."""
    # This would be implemented with proper IMAP mocking
    return None

@pytest.fixture
def sample_email_data():
    """Sample email data for testing."""
    return {
        "subject": "Test Email",
        "body": "This is a test email body",
        "from": "sender@example.com",
        "to": ["recipient@example.com"]
    }




