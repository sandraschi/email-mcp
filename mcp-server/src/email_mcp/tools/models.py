"""
Email MCP Models

Pydantic models and data structures for email services.
"""

from typing import Any, Dict
from pydantic import BaseModel, Field


class EmailServiceConfig(BaseModel):
    """Configuration for an email service."""
    name: str
    type: str  # smtp, api, webhook, local
    enabled: bool = True
    config: Dict[str, Any] = Field(default_factory=dict)