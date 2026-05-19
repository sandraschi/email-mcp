"""Lightweight AI router for the web dashboard — multi-provider (Ollama, LM Studio, OpenAI-compat, Anthropic)."""

from __future__ import annotations

import os
from typing import Any

import httpx
from fastmcp import FastMCP


class AIRouter:
    """Routes natural language chat queries to email tools via local or cloud LLM."""

    def __init__(self, mcp_app: FastMCP):
        self.mcp = mcp_app
        self.provider = os.getenv("AI_PROVIDER", "ollama")
        self.endpoint = os.getenv("AI_ENDPOINT", "http://localhost:11434/v1/chat/completions")
        self.model = os.getenv("AI_MODEL", "")

    _SYSTEM = (
        "You are the Email MCP AI Assistant. Help the user manage their email. "
        "Available tools: send_email, check_inbox, list_services, email_status, "
        "mailing_lists_catalog, mailing_list_latest, configure_service, email_help, "
        "suggest_email_subject, email_agentic_assist. "
        "Provide concise, direct responses. If a tool call is needed, describe it plainly. "
        "Do not hallucinate capabilities that don't exist."
    )

    async def route_query(self, query: str) -> str:
        """Route query through the configured AI provider."""
        return await self._route(query)

    _JSON_SYSTEM = "You are a JSON-only data extraction engine. Return ONLY valid JSON. No explanations, no markdown, no code fences, no prefixes. Just the raw JSON object."

    _WRITING_SYSTEM = "You are an expert email writing assistant. Rewrite and improve email text as requested. Return ONLY the rewritten text, no explanations, no prefixes, no notes."

    async def route_json_query(self, query: str) -> str:
        """Route query with a JSON-only system prompt."""
        return await self._route(query, system_prompt=self._JSON_SYSTEM)

    async def _route(self, query: str, system_prompt: str | None = None) -> str:
        """Route query with a specific system prompt."""
        provider = self.provider
        sp = system_prompt or self._SYSTEM

        async with httpx.AsyncClient(timeout=15.0) as client:
            if provider == "ollama":
                # Use sensible default model for Ollama if none configured
                if not self.model:
                    self.model = "llama3.1:8b"
                return await self._openai_compat(client, query, sp, self.endpoint or "http://localhost:11434/v1/chat/completions")
            elif provider == "lmstudio":
                return await self._openai_compat(client, query, sp, "http://localhost:1234/v1/chat/completions")
            elif provider == "openai":
                return await self._openai_compat(
                    client, query, sp,
                    self.endpoint or "https://api.openai.com/v1/chat/completions",
                    api_key=os.getenv("OPENAI_API_KEY", ""),
                )
            elif provider == "anthropic":
                return await self._anthropic(client, query, sp)
            elif provider == "google":
                return await self._openai_compat(
                    client, query, sp,
                    self.endpoint or "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
                    api_key=os.getenv("GOOGLE_API_KEY", ""),
                )
            else:
                return await self._openai_compat(client, query, sp, self.endpoint or "http://localhost:11434/v1/chat/completions")

    async def _openai_compat(
        self,
        client: httpx.AsyncClient,
        query: str,
        system_prompt: str | None = None,
        endpoint: str = "",
        api_key: str = "",
    ) -> str:
        sp = system_prompt or self._SYSTEM
        model = self.model or "gpt-4o-mini"
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        try:
            r = await client.post(
                endpoint,
                headers=headers,
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": sp},
                        {"role": "user", "content": query},
                    ],
                },
            )
            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]
            return f"Provider error {r.status_code}: {r.text[:200]}"
        except httpx.ConnectError:
            return f"Provider not reachable at {endpoint}. Configure a different provider in Settings."
        except Exception as exc:
            return f"Provider error: {exc}"

    async def _anthropic(self, client: httpx.AsyncClient, query: str, system_prompt: str | None = None) -> str:
        sp = system_prompt or self._SYSTEM
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key:
            return "ANTHROPIC_API_KEY not set. Configure it in Settings."
        model = self.model or "claude-haiku-4-5-20251001"
        try:
            r = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": model,
                    "max_tokens": 1024,
                    "system": sp,
                    "messages": [{"role": "user", "content": query}],
                },
            )
            if r.status_code == 200:
                return r.json()["content"][0]["text"]
            return f"Anthropic error {r.status_code}: {r.text[:200]}"
        except Exception as exc:
            return f"Anthropic error: {exc}"

    async def get_tools_list(self) -> list[dict[str, Any]]:
        """Return list of {name, description} dicts for all registered MCP tools."""
        tools = await self.mcp.list_tools()
        return [{"name": t.name, "description": getattr(t, "description", "") or ""} for t in tools]

    async def improve_text(self, text: str, style: str = "professional", length: str = "same", mood: str = "neutral") -> str:
        """Improve email body text with specified style, length, and mood."""
        query = (
            f"Improve this email body. Make it {style} in tone, make it {length} in length, "
            f"and make the mood {mood}.\n"
            "Return ONLY the improved text, no explanations, no prefixes.\n\n"
            f"---\n{text[:3000]}"
        )
        return await self.route_query(query)
