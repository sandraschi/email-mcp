from typing import List
from fastmcp import FastMCP
import os


class AIRouter:
    """Standard AI router for Email Hub natural language processing."""

    def __init__(self, mcp_app: FastMCP):
        self.mcp = mcp_app
        self.provider = os.getenv("AI_PROVIDER", "ollama")
        self.endpoint = os.getenv("AI_ENDPOINT", "http://localhost:11434/api/generate")
        self.model = os.getenv("AI_MODEL", "llama3.1-8b")

    async def route_query(self, query: str) -> str:
        """Route natural language query to Email tools using AI reasoning."""
        # Standard placeholder for SOTA AI routing
        return f"AI analysis of: {query}. Routing to appropriate Email tool..."

    async def get_tools_list(self) -> List[str]:
        """Get list of registered MCP tools (FastMCP 3 list_tools returns list)."""
        tools = await self.mcp.list_tools()
        return [t.name for t in tools]
