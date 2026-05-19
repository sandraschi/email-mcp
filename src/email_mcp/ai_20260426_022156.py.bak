"""Lightweight AI router for the web dashboard (optional local LLM)."""

import os
from typing import List

from fastmcp import FastMCP


class AIRouter:
    """Standard AI router for Email MCP natural language processing."""

    def __init__(self, mcp_app: FastMCP):
        self.mcp = mcp_app
        self.provider = os.getenv("AI_PROVIDER", "ollama")
        self.endpoint = os.getenv("AI_ENDPOINT", "http://localhost:11434/api/generate")
        self.model = os.getenv("AI_MODEL", "llama3.1-8b")

    async def route_query(self, query: str) -> str:
        """Route natural language query to Email tools using AI reasoning (no gaslights)."""
        import httpx
        
        system_prompt = (
            "You are the Email MCP AI Assistant. Based on the user's request, "
            "determine which email tools to use (send_email, check_inbox, list_services, "
            "email_status, mailing_lists_catalog, mailing_list_latest). "
            "Provide a brief, helpful response or a plan. If you can't satisfy the "
            "request, be honest."
        )

        if self.provider == "ollama":
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(
                        self.endpoint,
                        json={
                            "model": self.model,
                            "prompt": f"{system_prompt}\n\nUser: {query}\n\nAssistant:",
                            "stream": False
                        }
                    )
                    if response.status_code == 200:
                        return response.json().get("response", "No response from AI.")
            except Exception as e:
                return f"AI Provider (Ollama) unreachable: {str(e)}. Fallback: I can help you with send_email, check_inbox, or email_status."
        
        # Transparent fallback if provider is not configured or unsupported
        return f"Query received: '{query}'. AI routing is currently in fallback mode. Available tools: {', '.join(await self.get_tools_list())}."

    async def get_tools_list(self) -> List[str]:
        """Get list of registered MCP tools."""
        tools = await self.mcp.list_tools()
        return [t.name for t in tools]
