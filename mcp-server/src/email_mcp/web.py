from fastapi import FastAPI, Body, Depends
from fastmcp import FastMCP
from .ai import AIRouter
from .auth import authenticate


def setup_webapp(app: FastAPI, mcp_app: FastMCP):
    """Setup standard SOTA web endpoints for Email Hub MCP."""
    ai_router = AIRouter(mcp_app)

    @app.get("/api/status")
    async def get_status(user: str = Depends(authenticate)):
        return {"status": "connected", "user": user, "mcp": mcp_app.name}

    @app.get("/api/tools")
    async def list_tools(user: str = Depends(authenticate)):
        tools = await ai_router.get_tools_list()
        return {"tools": tools}

    @app.post("/api/chat")
    async def chat(query: str = Body(..., embed=True), user: str = Depends(authenticate)):
        response = await ai_router.route_query(query)
        return {"response": response}

    # Skill content (FastMCP 3.1) — SOTA page: show skill so client/IDE knows how to use the server
    @app.get("/api/skills")
    async def list_skills(user: str = Depends(authenticate)):
        """List skills exposed by the MCP server (skill:// URIs ending with /SKILL.md)."""
        resources = await mcp_app.list_resources()
        skills = []
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
                        text += p["text"]
            return {"name": name, "uri": uri, "content": text or "(empty)"}
        except Exception as e:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail=f"Skill not found: {name}") from e
