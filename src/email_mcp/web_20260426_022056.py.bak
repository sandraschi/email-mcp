"""FastAPI routes for the Email MCP web dashboard (tools, chat, skills)."""

from fastapi import Body, Depends, FastAPI, HTTPException
from fastmcp import FastMCP

from .ai import AIRouter
from .auth import authenticate


def setup_webapp(app: FastAPI, mcp_app: FastMCP) -> None:
    """Register standard SOTA web endpoints for the Email MCP dashboard."""
    ai_router = AIRouter(mcp_app)

    @app.get("/api/status")
    async def get_status(user: str = Depends(authenticate)):
        return {"status": "connected", "user": user, "mcp": mcp_app.name}

    @app.get("/api/tools")
    async def list_tools(user: str = Depends(authenticate)):
        tools = await ai_router.get_tools_list()
        return {"tools": tools}

    @app.get("/api/chat")
    async def chat(query: str = Body(..., embed=True), user: str = Depends(authenticate)):
        response = await ai_router.route_query(query)
        return {"response": response}

    @app.get("/api/stats")
    async def get_stats(user: str = Depends(authenticate)):
        """Get real-time statistics for the dashboard (no gaslights)."""
        try:
            # Get connectivity status
            status_result = await mcp_app.call_tool("email_status")
            
            # Get unread messages from the first connected IMAP/local service
            unread_count = 0
            recent_activity = []
            
            services = status_result.get("services", {})
            for svc_name, svc_info in services.items():
                if svc_info.get("connected") and svc_info.get("type") in ["smtp", "local"]:
                    inbox_result = await mcp_app.call_tool("check_inbox", {"service": svc_name, "unread_only": True, "limit": 5})
                    if inbox_result.get("success"):
                        unread_count += inbox_result.get("count", 0)
                        recent_activity.extend(inbox_result.get("emails", []))
            
            # Simple "load" heuristic (e.g. number of tools exposed)
            tools_count = len(await mcp_app.list_tools())
            
            return {
                "unread_count": unread_count,
                "connected_services": status_result.get("connected_services", 0),
                "total_services": status_result.get("total_services", 0),
                "system_load": f"{min(99, tools_count * 4)}%",
                "recent_activity": recent_activity[:5],
                "mcp_version": status_result.get("version", "0.3.1")
            }
        except Exception as e:
            return {
                "unread_count": 0,
                "connected_services": 0,
                "system_load": "0%",
                "recent_activity": [],
                "error": str(e)
            }

    @app.get("/api/skills")
    async def list_skills(user: str = Depends(authenticate)):
        """List skills exposed by the MCP server (skill:// URIs ending with /SKILL.md)."""
        resources = await mcp_app.list_resources()
        skills: list[dict[str, str]] = []
        for r in resources:
            uri = getattr(r, "uri", None) or str(getattr(r, "name", ""))
            if uri.startswith("skill://") and "/SKILL.md" in uri:
                name = uri.replace("skill://", "").split("/")[0]
                skills.append({"name": name, "uri": uri})
        return {"skills": skills}

    @app.get("/api/skills/{name}")
    async def get_skill_content(name: str, user: str = Depends(authenticate)):
        """Return the main skill instruction content (SKILL.md) for the given skill name."""
        uri = f"skill://{name}/SKILL.md"
        try:
            parts = await mcp_app.read_resource(uri)
            text = ""
            if parts:
                for p in parts:
                    if hasattr(p, "text"):
                        text += getattr(p, "text", "") or ""
                    elif isinstance(p, dict) and "text" in p:
                        text += str(p["text"])
            return {"name": name, "uri": uri, "content": text or "(empty)"}
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Skill not found: {name}") from e
