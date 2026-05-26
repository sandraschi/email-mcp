"""FastAPI routes for the Email MCP web dashboard.

Endpoints:
    GET  /api/status              — server health
    GET  /api/capabilities        — feature flags for runtime gating
    GET  /api/tools               — list MCP tools
    GET  /api/stats               — KPI stats for dashboard
    GET  /api/services            — list + connectivity of all services
    GET  /api/services/{name}     — single service config
    POST /api/services            — add a new service
    PUT  /api/services/{name}     — update service config
    DELETE /api/services/{name}   — remove a service
    GET  /api/inbox               — fetch inbox (service, folder, limit, unread_only)
    GET  /api/inbox/{message_id}  — fetch single email with full body
    POST /api/inbox/{message_id}/mark-read  — mark as read
    POST /api/inbox/{message_id}/unread      — mark as unread
    DELETE /api/inbox/{message_id} — delete email
    GET  /api/search              — search emails via IMAP
    POST /api/send                — send email
    GET  /api/skills              — list skill:// resources
    GET  /api/skills/{name}       — skill markdown content
    GET  /api/llm/models          — probe local LLM providers (Ollama/LM Studio)
    POST /api/llm/configure       — update AI provider settings at runtime
    POST /api/chat                — natural language → AI router
    GET  /api/drafts              — list drafts
    POST /api/drafts              — save draft
    PUT  /api/drafts/{draft_id}   — update draft
    DELETE /api/drafts/{draft_id} — delete draft
"""

from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any

import httpx
from fastapi import Body, Depends, FastAPI, HTTPException
from fastmcp import FastMCP

from .ai import AIRouter
from .auth import authenticate


def _extract_tool_result(result: Any) -> dict[str, Any]:
    """Extract a plain dict from an MCP call_tool result.

    FastMCP 3.2 call_tool returns CallToolResult which may have a nested
    TextContent dict inside a content[0].text JSON string.
    """
    if isinstance(result, dict):
        return result
    if hasattr(result, "content") and isinstance(result.content, list) and len(result.content) > 0:
        item = result.content[0]
        if hasattr(item, "text"):
            try:
                return json.loads(item.text)
            except (json.JSONDecodeError, TypeError, ValueError):
                pass
        elif isinstance(item, dict) and "text" in item:
            try:
                return json.loads(item["text"])
            except (json.JSONDecodeError, TypeError, ValueError):
                pass
    return {"result": str(result) if result is not None else None}


# In-memory draft store (survives one process lifetime)
_drafts: dict[str, dict[str, Any]] = {}
_DRAFTS_FILE = Path(os.getenv("EMAIL_MCP_DRAFTS_FILE", Path(__file__).resolve().parent.parent / "drafts.json"))


def _load_drafts() -> dict[str, dict[str, Any]]:
    global _drafts
    try:
        if _DRAFTS_FILE.is_file():
            _drafts = json.loads(_DRAFTS_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return _drafts


def _save_drafts() -> None:
    try:
        _DRAFTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        _DRAFTS_FILE.write_text(json.dumps(_drafts, indent=2, default=str), encoding="utf-8")
    except Exception:
        pass


def setup_webapp(app: FastAPI, mcp_app: FastMCP) -> None:
    """Register all SOTA web endpoints for the Email MCP dashboard."""
    ai_router = AIRouter(mcp_app)
    _load_drafts()

    # ── Basic health ──────────────────────────────────────────────────────────

    @app.get("/api/status")
    async def get_status(user: str = Depends(authenticate)):
        return {"status": "connected", "user": user, "mcp": mcp_app.name, "version": "0.4.1"}

    @app.get("/api/capabilities")
    async def get_capabilities(_user: str = Depends(authenticate)):
        tools = await mcp_app.list_tools()
        tool_names = {t.name for t in tools}
        has_imap = any(n in tool_names for n in ("check_inbox", "mailing_list_latest", "fetch_email_detail"))
        has_send = "send_email" in tool_names
        has_sampling = any(n in tool_names for n in ("suggest_email_subject", "email_agentic_assist"))
        has_prefab = any(n in tool_names for n in ("show_email_status_card", "show_inbox_card"))
        return {
            "inbox": has_imap,
            "send": has_send,
            "sampling": has_sampling,
            "prefab": has_prefab,
            "agentic_workflows": has_sampling,
            "mailing_lists": "mailing_lists_catalog" in tool_names,
            "local_llm_autodiscovery": True,
            "multi_provider": True,
            "search": "search_emails" in tool_names,
            "detail": "fetch_email_detail" in tool_names,
            "delete": "delete_email" in tool_names,
            "drafts": True,
            "workflows": True,
            "contacts": True,
            "watcher": True,
            "auto_respond": True,
        }

    # ── Tools ────────────────────────────────────────────────────────────────

    @app.get("/api/tools")
    async def list_tools(_user: str = Depends(authenticate)):
        tools = await ai_router.get_tools_list()
        return {"tools": tools}

    # ── Services ─────────────────────────────────────────────────────────────

    @app.get("/api/services")
    async def list_services(_user: str = Depends(authenticate)):
        try:
            result = _extract_tool_result(await mcp_app.call_tool("email_status"))
            return result
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.get("/api/services/{name}")
    async def get_service(name: str, _user: str = Depends(authenticate)):
        try:
            result = _extract_tool_result(await mcp_app.call_tool("list_services"))
            svcs = result.get("services", {})
            if name not in svcs:
                raise HTTPException(status_code=404, detail=f"Service {name!r} not found")
            return {"service": {name: svcs[name]}}
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.post("/api/services")
    async def add_service(
        payload: dict[str, Any] = Body(...),
        _user: str = Depends(authenticate),
    ):
        required = {"name", "type", "config"}
        missing = required - set(payload.keys())
        if missing:
            raise HTTPException(status_code=422, detail=f"Missing fields: {missing}")
        try:
            result = _extract_tool_result(
                await mcp_app.call_tool(
                    "configure_service",
                    {
                        "name": payload["name"],
                        "type": payload["type"],
                        "config": payload["config"],
                        "enabled": payload.get("enabled", True),
                    },
                )
            )
            return result
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.put("/api/services/{name}")
    async def update_service(
        name: str,
        payload: dict[str, Any] = Body(...),
        _user: str = Depends(authenticate),
    ):
        try:
            rm_ = _extract_tool_result(await mcp_app.call_tool("remove_service", {"name": name}))
            if not rm_.get("success"):
                return rm_
            cfg = payload.get("config", {})
            result = _extract_tool_result(
                await mcp_app.call_tool(
                    "configure_service",
                    {
                        "name": name,
                        "type": payload.get("type", cfg.get("type", "smtp")),
                        "config": cfg,
                        "enabled": payload.get("enabled", True),
                    },
                )
            )
            return result
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.delete("/api/services/{name}")
    async def delete_service(name: str, _user: str = Depends(authenticate)):
        try:
            result = _extract_tool_result(await mcp_app.call_tool("remove_service", {"name": name}))
            return result
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.post("/api/services/{name}/test")
    async def test_service(name: str, _user: str = Depends(authenticate)):
        try:
            result = _extract_tool_result(await mcp_app.call_tool("email_status", {"service": name}))
            return result
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.post("/api/services/quick")
    async def quick_setup(
        payload: dict[str, Any] = Body(...),
        _user: str = Depends(authenticate),
    ):
        """Quick-setup a provider with email + password only."""
        provider = payload.get("provider", "").strip().lower()
        email = payload.get("email", "").strip()
        password = payload.get("password", "").strip()
        if not provider or not email or not password:
            raise HTTPException(status_code=422, detail="provider, email, and password are required")

        PROFILES: dict[str, dict[str, Any]] = {
            "gmail": {
                "name": "gmail",
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "imap_server": "imap.gmail.com",
                "imap_port": 993,
            },
            "outlook": {
                "name": "outlook",
                "smtp_server": "smtp-mail.outlook.com",
                "smtp_port": 587,
                "imap_server": "outlook.office365.com",
                "imap_port": 993,
            },
            "hotmail": {
                "name": "outlook",
                "smtp_server": "smtp-mail.outlook.com",
                "smtp_port": 587,
                "imap_server": "outlook.office365.com",
                "imap_port": 993,
            },
            "yahoo": {
                "name": "yahoo",
                "smtp_server": "smtp.mail.yahoo.com",
                "smtp_port": 587,
                "imap_server": "imap.mail.yahoo.com",
                "imap_port": 993,
            },
            "icloud": {
                "name": "icloud",
                "smtp_server": "smtp.mail.me.com",
                "smtp_port": 587,
                "imap_server": "imap.mail.me.com",
                "imap_port": 993,
            },
            "protonmail": {
                "name": "protonmail",
                "smtp_server": "mail.protonmail.com",
                "smtp_port": 587,
                "imap_server": "mail.protonmail.com",
                "imap_port": 993,
            },
            "zoho": {
                "name": "zoho",
                "smtp_server": "smtp.zoho.com",
                "smtp_port": 587,
                "imap_server": "imap.zoho.com",
                "imap_port": 993,
            },
            "gmx": {
                "name": "gmx",
                "smtp_server": "smtp.gmx.com",
                "smtp_port": 587,
                "imap_server": "imap.gmx.com",
                "imap_port": 993,
            },
            "fastmail": {
                "name": "fastmail",
                "smtp_server": "smtp.fastmail.com",
                "smtp_port": 587,
                "imap_server": "imap.fastmail.com",
                "imap_port": 993,
            },
        }

        if provider not in PROFILES:
            raise HTTPException(status_code=422, detail=f"Unknown provider '{provider}'. Supported: {', '.join(PROFILES.keys())}")

        profile = PROFILES[provider]
        svc_name = profile["name"]
        config = {
            "smtp_server": profile["smtp_server"],
            "smtp_port": profile["smtp_port"],
            "smtp_user": email,
            "smtp_password": password,
            "smtp_from": email,
            "imap_server": profile["imap_server"],
            "imap_port": profile["imap_port"],
            "imap_user": email,
            "imap_password": password,
        }
        result = _extract_tool_result(
            await mcp_app.call_tool(
                "configure_service",
                {"name": svc_name, "type": "smtp", "config": config},
            )
        )
        return result

    @app.post("/api/services/check-bridge")
    async def check_proton_bridge(_user: str = Depends(authenticate)):
        """Check if ProtonMail Bridge is running and accessible.

        Returns:
          running: bool — Bridge process found running
          ports_open: [int] — which SMTP/IMAP ports respond
          install_url: str — download link
          message: str — human-readable status
        """
        import socket
        import subprocess

        result = {"bridge_running": False, "ports_open": [], "install_url": "https://proton.me/mail/bridge", "message": ""}

        # 1. Check for Bridge process (tasklist is a Windows built-in, safe)
        try:
            procs = subprocess.run(["tasklist", "/FI", "IMAGENAME eq protonmail-bridge*"], capture_output=True, text=True, timeout=5)
            if "protonmail" in procs.stdout.lower():
                result["bridge_running"] = True
        except Exception:
            pass
        if not result["bridge_running"]:
            try:
                procs = subprocess.run(["tasklist", "/FI", "IMAGENAME eq bridge*"], capture_output=True, text=True, timeout=5)
                if "bridge" in procs.stdout.lower():
                    result["bridge_running"] = True
            except Exception:
                pass

        # 2. Check ports 1025 (SMTP) and 1143 (IMAP) — these are Bridge's default ports
        for port in [1025, 1143]:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(2)
                s.connect(("127.0.0.1", port))
                s.close()
                result["ports_open"].append(port)
            except Exception:
                pass

        # 3. Build message
        smtp_ok = 1025 in result["ports_open"]
        imap_ok = 1143 in result["ports_open"]
        if result["bridge_running"] and smtp_ok and imap_ok:
            result["message"] = "ProtonMail Bridge is running. (Note: Bridge now requires a paid ProtonMail subscription.)"
            result["status"] = "ready"
        elif result["bridge_running"] and not (smtp_ok and imap_ok):
            result["message"] = "Bridge process found but ports not responding. Restart Bridge."
            result["status"] = "bridge_port_error"
        elif not result["bridge_running"] and (smtp_ok and imap_ok):
            result["message"] = "Ports 1025/1143 open but Bridge not detected. Something else is using them."
            result["status"] = "unknown_service"
        else:
            result["message"] = "ProtonMail Bridge not found. Note: Since late 2023, Bridge and SMTP/IMAP require a paid ProtonMail subscription (Mail Plus €3.99/mo). Free accounts cannot connect via SMTP/IMAP."
            result["status"] = "not_installed"

        return result

    # ── Stats (dashboard KPIs) ───────────────────────────────────────────────

    @app.get("/api/stats")
    async def get_stats(_user: str = Depends(authenticate)):
        try:
            status_result = _extract_tool_result(await mcp_app.call_tool("email_status"))
            unread_count = 0
            recent_activity: list[dict[str, Any]] = []

            services = status_result.get("services", {})
            for svc_name, svc_info in services.items():
                if svc_info.get("connected") and svc_info.get("type") in ("smtp", "local"):
                    try:
                        inbox_result = _extract_tool_result(
                            await mcp_app.call_tool(
                                "check_inbox",
                                {"service": svc_name, "unread_only": True, "limit": 5},
                            )
                        )
                        if inbox_result.get("success"):
                            unread_count += inbox_result.get("count", 0)
                            for email in inbox_result.get("emails", []):
                                email["_service"] = svc_name
                            recent_activity.extend(inbox_result.get("emails", []))
                    except Exception:
                        pass

            tools_count = len(await mcp_app.list_tools())
            return {
                "unread_count": unread_count,
                "connected_services": status_result.get("connected_services", 0),
                "total_services": status_result.get("total_services", 0),
                "configured_services": status_result.get("configured_services", 0),
                "tools_count": tools_count,
                "drafts_count": len(_drafts),
                "recent_activity": recent_activity[:5],
                "mcp_version": status_result.get("version", "0.3.2"),
            }
        except Exception as exc:
            return {
                "unread_count": 0,
                "connected_services": 0,
                "total_services": 0,
                "configured_services": 0,
                "tools_count": 0,
                "drafts_count": 0,
                "recent_activity": [],
                "mcp_version": "0.3.2",
                "error": str(exc),
            }

    # ── Inbox ────────────────────────────────────────────────────────────────

    @app.get("/api/inbox")
    async def get_inbox(
        service: str = "default",
        folder: str = "INBOX",
        limit: int = 20,
        unread_only: bool = False,
        from_contains: str = "",
        subject_contains: str = "",
        _user: str = Depends(authenticate),
    ):
        try:
            return _extract_tool_result(
                await mcp_app.call_tool(
                    "check_inbox",
                    {
                        "service": service,
                        "folder": folder,
                        "limit": limit,
                        "unread_only": unread_only,
                        "from_contains": from_contains or None,
                        "subject_contains": subject_contains or None,
                    },
                )
            )
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.get("/api/inbox/{message_id}")
    async def get_email_detail(
        message_id: str,
        service: str = "default",
        folder: str = "INBOX",
        _user: str = Depends(authenticate),
    ):
        try:
            result = _extract_tool_result(
                await mcp_app.call_tool(
                    "fetch_email_detail",
                    {"email_id": message_id, "service": service, "folder": folder},
                )
            )
            if not result.get("success"):
                raise HTTPException(status_code=404, detail=result.get("error", "Not found"))
            return result
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.post("/api/inbox/{message_id}/mark-read")
    async def mark_email_as_read(
        message_id: str,
        payload: dict[str, Any] = Body(default={}),
        _user: str = Depends(authenticate),
    ):
        try:
            return _extract_tool_result(
                await mcp_app.call_tool(
                    "mark_email_read",
                    {
                        "email_id": message_id,
                        "service": payload.get("service", "default"),
                        "folder": payload.get("folder", "INBOX"),
                    },
                )
            )
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.post("/api/inbox/{message_id}/unread")
    async def mark_email_as_unread(
        message_id: str,
        payload: dict[str, Any] = Body(default={}),
        _user: str = Depends(authenticate),
    ):
        try:
            return _extract_tool_result(
                await mcp_app.call_tool(
                    "mark_email_unread",
                    {
                        "email_id": message_id,
                        "service": payload.get("service", "default"),
                        "folder": payload.get("folder", "INBOX"),
                    },
                )
            )
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.delete("/api/inbox/{message_id}")
    async def delete_email(
        message_id: str,
        service: str = "default",
        folder: str = "INBOX",
        _user: str = Depends(authenticate),
    ):
        try:
            return _extract_tool_result(
                await mcp_app.call_tool(
                    "delete_email",
                    {"email_id": message_id, "service": service, "folder": folder},
                )
            )
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    # ── Search ───────────────────────────────────────────────────────────────

    @app.get("/api/search")
    async def search_emails(
        q: str = "",
        service: str = "default",
        folder: str = "INBOX",
        limit: int = 20,
        _user: str = Depends(authenticate),
    ):
        if not q.strip():
            raise HTTPException(status_code=422, detail="q (query) is required")
        try:
            return _extract_tool_result(
                await mcp_app.call_tool(
                    "search_emails",
                    {"query": q.strip(), "service": service, "folder": folder, "limit": limit},
                )
            )
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    # ── Folders (IMAP) ───────────────────────────────────────────────────────

    @app.get("/api/services/{name}/folders")
    async def list_folders(name: str, _user: str = Depends(authenticate)):
        try:
            return _extract_tool_result(await mcp_app.call_tool("list_folders", {"service": name}))
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.post("/api/services/{name}/folders")
    async def create_folder(
        name: str,
        payload: dict[str, Any] = Body(...),
        _user: str = Depends(authenticate),
    ):
        folder = payload.get("folder", "").strip()
        if not folder:
            raise HTTPException(status_code=422, detail="folder is required")
        try:
            return _extract_tool_result(await mcp_app.call_tool("create_folder", {"folder": folder, "service": name}))
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.delete("/api/services/{name}/folders/{folder_name:path}")
    async def delete_folder(
        name: str,
        folder_name: str,
        _user: str = Depends(authenticate),
    ):
        try:
            return _extract_tool_result(await mcp_app.call_tool("delete_folder", {"folder": folder_name, "service": name}))
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.put("/api/services/{name}/folders/{folder_name:path}")
    async def rename_folder(
        name: str,
        folder_name: str,
        payload: dict[str, Any] = Body(...),
        _user: str = Depends(authenticate),
    ):
        new_name = payload.get("new_name", "").strip()
        if not new_name:
            raise HTTPException(status_code=422, detail="new_name is required")
        try:
            return _extract_tool_result(await mcp_app.call_tool("rename_folder", {"old_name": folder_name, "new_name": new_name, "service": name}))
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.get("/api/inbox/{message_id}/attachment/{part_index}")
    async def get_attachment(
        message_id: str,
        part_index: int,
        service: str = "default",
        folder: str = "INBOX",
        _user: str = Depends(authenticate),
    ):
        """Download an email attachment by MIME part index."""
        import asyncio
        import imaplib
        from email import message_from_bytes

        from fastapi.responses import Response

        service_obj = mcp_app.services.get(service) if hasattr(mcp_app, "services") else None
        if not service_obj or not hasattr(service_obj, "imap_server"):
            raise HTTPException(status_code=400, detail="Service does not support IMAP")
        try:

            def fetch_attachment():
                mail = imaplib.IMAP4_SSL(service_obj.imap_server, service_obj.imap_port)
                mail.login(service_obj.imap_user, service_obj.imap_password)
                mail.select(folder)
                eid = message_id.encode() if isinstance(message_id, str) else message_id
                status, data = mail.fetch(eid, "(RFC822)")
                mail.close()
                mail.logout()
                if status != "OK":
                    return None
                msg = message_from_bytes(data[0][1])
                idx = 0
                for part in msg.walk():
                    cd = str(part.get("Content-Disposition", ""))
                    if "attachment" in cd.lower() or ("filename" in cd.lower() and part.get_content_maintype() not in ("text", "multipart")):
                        idx += 1
                        if idx == part_index:
                            return {
                                "data": part.get_payload(decode=True),
                                "content_type": part.get_content_type(),
                                "filename": part.get_filename() or f"attachment-{part_index}",
                            }
                return None

            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, fetch_attachment)
            if not result:
                raise HTTPException(status_code=404, detail="Attachment not found")
            return Response(content=result["data"], media_type=result["content_type"], headers={"Content-Disposition": f'attachment; filename="{result["filename"]}"'})
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.get("/api/inbox/unified")
    async def get_unified_inbox(
        limit: int = 20,
        unread_only: bool = False,
        _user: str = Depends(authenticate),
    ):
        """Fetch emails from all configured services merged by date."""
        status_result = _extract_tool_result(await mcp_app.call_tool("email_status"))
        services = status_result.get("services", {})
        all_emails = []
        errors: list[str] = []
        for svc_name, svc_info in services.items():
            if not svc_info.get("connected"):
                continue
            if svc_info.get("type") not in ("smtp", "local"):
                continue
            try:
                result = _extract_tool_result(
                    await mcp_app.call_tool(
                        "check_inbox",
                        {"service": svc_name, "limit": limit, "unread_only": unread_only},
                    )
                )
                if result.get("success"):
                    for email in result.get("emails", []):
                        email["_service"] = svc_name
                        all_emails.append(email)
            except Exception as e:
                errors.append(f"{svc_name}: {e}")
        # Sort by date descending (most recent first)
        all_emails.sort(key=lambda e: e.get("date", ""), reverse=True)
        return {"emails": all_emails[:limit], "count": len(all_emails), "total": len(all_emails), "errors": errors}

    # ── Send ─────────────────────────────────────────────────────────────────

    @app.post("/api/send")
    async def send_email(
        payload: dict[str, Any] = Body(...),
        _user: str = Depends(authenticate),
    ):
        required = {"to", "subject", "body"}
        missing = required - set(payload.keys())
        if missing:
            raise HTTPException(status_code=422, detail=f"Missing fields: {missing}")
        try:
            result = _extract_tool_result(
                await mcp_app.call_tool(
                    "send_email",
                    {
                        "to": payload["to"],
                        "subject": payload["subject"],
                        "body": payload["body"],
                        "service": payload.get("service", "default"),
                        "html": payload.get("html"),
                        "cc": payload.get("cc"),
                        "bcc": payload.get("bcc"),
                    },
                )
            )
            return result
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.post("/api/send-bulk")
    async def send_bulk(
        payload: dict[str, Any] = Body(...),
        _user: str = Depends(authenticate),
    ):
        """Send the same email to multiple recipients with rate limiting.

        Max 50 recipients per batch. Includes anti-spam warnings.
        """
        recipients = payload.get("to", [])
        if isinstance(recipients, str):
            recipients = [r.strip() for r in recipients.replace("\n", ",").split(",") if r.strip()]
        if not isinstance(recipients, list):
            recipients = [str(recipients)]
        recipients = [r.strip() for r in recipients if r.strip()]

        if len(recipients) == 0:
            raise HTTPException(status_code=422, detail="No valid recipients")
        if len(recipients) > 50:
            raise HTTPException(status_code=422, detail=f"Too many recipients ({len(recipients)}). Max 50 per batch. Bulk operations require review.")
        if len(recipients) > 10 and not payload.get("confirmed"):
            return {
                "success": False,
                "needs_confirmation": True,
                "count": len(recipients),
                "warning": f"Sending to {len(recipients)} recipients. Unsolicited bulk email (spam) is illegal under CAN-SPAM Act, GDPR, and many other laws. Only proceed with explicit consent from every recipient.",
                "message": "Large batch requires confirmation",
            }

        subject = payload.get("subject", "").strip()
        body = payload.get("body", "").strip()
        if not subject or not body:
            raise HTTPException(status_code=422, detail="subject and body are required")

        service = payload.get("service", "default")
        results: list[dict[str, Any]] = []
        success_count = 0
        fail_count = 0

        for _i, to in enumerate(recipients):
            try:
                result = _extract_tool_result(
                    await mcp_app.call_tool(
                        "send_email",
                        {"to": to, "subject": subject, "body": body, "service": service},
                    )
                )
                if result.get("success"):
                    success_count += 1
                else:
                    fail_count += 1
                results.append({"to": to, "success": result.get("success", False), "error": result.get("error")})
            except Exception as exc:
                fail_count += 1
                results.append({"to": to, "success": False, "error": str(exc)})

        return {
            "success": True,
            "total": len(recipients),
            "sent": success_count,
            "failed": fail_count,
            "results": results,
        }

    # ── Drafts ───────────────────────────────────────────────────────────────

    @app.get("/api/drafts")
    async def list_drafts(_user: str = Depends(authenticate)):
        return {
            "drafts": [
                {
                    "id": d["id"],
                    "to": d.get("to", ""),
                    "subject": d.get("subject", ""),
                    "updated_at": d.get("updated_at", ""),
                    "service": d.get("service", "default"),
                }
                for d in _drafts.values()
            ],
            "count": len(_drafts),
        }

    @app.post("/api/drafts")
    async def save_draft(
        payload: dict[str, Any] = Body(...),
        _user: str = Depends(authenticate),
    ):
        draft_id = payload.get("id") or str(uuid.uuid4())[:8]
        draft = {
            "id": draft_id,
            "to": payload.get("to", ""),
            "cc": payload.get("cc", ""),
            "subject": payload.get("subject", ""),
            "body": payload.get("body", ""),
            "html": payload.get("html"),
            "service": payload.get("service", "default"),
            "updated_at": int(time.time()),
        }
        _drafts[draft_id] = draft
        _save_drafts()
        return {"success": True, "draft": draft, "message": f"Draft {draft_id!r} saved"}

    @app.put("/api/drafts/{draft_id}")
    async def update_draft(
        draft_id: str,
        payload: dict[str, Any] = Body(...),
        _user: str = Depends(authenticate),
    ):
        if draft_id not in _drafts:
            raise HTTPException(status_code=404, detail=f"Draft {draft_id!r} not found")
        existing = _drafts[draft_id]
        for key in ("to", "cc", "subject", "body", "html", "service"):
            if key in payload:
                existing[key] = payload[key]
        existing["updated_at"] = int(time.time())
        _save_drafts()
        return {"success": True, "draft": existing, "message": f"Draft {draft_id!r} updated"}

    @app.delete("/api/drafts/{draft_id}")
    async def delete_draft(draft_id: str, _user: str = Depends(authenticate)):
        if draft_id not in _drafts:
            raise HTTPException(status_code=404, detail=f"Draft {draft_id!r} not found")
        del _drafts[draft_id]
        _save_drafts()
        return {"success": True, "message": f"Draft {draft_id!r} deleted"}

    # ── Contacts ──────────────────────────────────────────────────────────────

    @app.get("/api/contacts")
    async def list_contacts(
        q: str = "",
        _user: str = Depends(authenticate),
    ):
        from .contacts import list_contacts as lc
        from .contacts import search_contacts

        if q.strip():
            return {"contacts": search_contacts(q.strip())}
        return {"contacts": lc()}

    @app.post("/api/contacts")
    async def add_contact(
        payload: dict[str, Any] = Body(...),
        _user: str = Depends(authenticate),
    ):
        from .contacts import add_contact as ac

        name = payload.get("name", "").strip()
        email = payload.get("email", "").strip()
        if not email:
            raise HTTPException(status_code=422, detail="email is required")
        result = ac(name, email, payload.get("phone", ""), payload.get("notes", ""), payload.get("group", ""))
        return result

    @app.put("/api/contacts/{contact_id}")
    async def update_contact(
        contact_id: str,
        payload: dict[str, Any] = Body(...),
        _user: str = Depends(authenticate),
    ):
        from .contacts import update_contact as uc

        return uc(contact_id, payload)

    @app.delete("/api/contacts/{contact_id}")
    async def delete_contact(contact_id: str, _user: str = Depends(authenticate)):
        from .contacts import delete_contact as dc

        return dc(contact_id)

    @app.post("/api/contacts/import")
    async def import_contacts(
        payload: dict[str, Any] = Body(...),
        _user: str = Depends(authenticate),
    ):
        from .contacts import import_csv, import_vcard

        fmt = payload.get("format", "csv")
        text = payload.get("text", "")
        if not text:
            raise HTTPException(status_code=422, detail="text is required")
        if fmt == "csv":
            return import_csv(text)
        elif fmt == "vcard":
            return import_vcard(text)
        raise HTTPException(status_code=422, detail="format must be 'csv' or 'vcard'")

    @app.post("/api/contacts/import-google")
    async def import_google_contacts(
        payload: dict[str, Any] = Body(...),
        _user: str = Depends(authenticate),
    ):
        from .contacts import import_google

        token = payload.get("token", "").strip()
        if not token:
            raise HTTPException(status_code=422, detail="OAuth token is required")
        return await import_google(token)

    @app.post("/api/contacts/import-microsoft")
    async def import_microsoft_contacts(
        payload: dict[str, Any] = Body(...),
        _user: str = Depends(authenticate),
    ):
        from .contacts import import_microsoft

        token = payload.get("token", "").strip()
        if not token:
            raise HTTPException(status_code=422, detail="OAuth token is required")
        return await import_microsoft(token)

    @app.get("/api/contacts/groups")
    async def list_groups(_user: str = Depends(authenticate)):
        from .contacts import get_groups

        return {"groups": get_groups()}

    @app.get("/api/curated-lists")
    async def curated_list_lists(_user: str = Depends(authenticate)):
        from .curated_lists import list_lists

        return {"lists": list_lists()}

    @app.get("/api/curated-lists/{list_id}")
    async def curated_list_detail(list_id: str, _user: str = Depends(authenticate)):
        from .curated_lists import get_list

        lst = get_list(list_id)
        if not lst:
            raise HTTPException(status_code=404, detail=f"List {list_id!r} not found")
        return {"list": lst}

    @app.post("/api/curated-lists/{list_id}/import")
    async def curated_list_import(list_id: str, _user: str = Depends(authenticate)):
        from .curated_lists import import_list

        return import_list(list_id)

    # ── Templates ─────────────────────────────────────────────────────────────

    @app.get("/api/templates")
    async def template_list(_user: str = Depends(authenticate)):
        from .templates import list_templates

        return {"templates": list_templates()}

    @app.post("/api/templates")
    async def template_add(
        payload: dict[str, Any] = Body(...),
        _user: str = Depends(authenticate),
    ):
        from .templates import add_template

        name = payload.get("name", "").strip()
        if not name:
            raise HTTPException(status_code=422, detail="name is required")
        return add_template(name, payload.get("subject", ""), payload.get("body", ""), payload.get("html", ""), payload.get("category", ""))

    @app.delete("/api/templates/{template_id}")
    async def template_delete(template_id: str, _user: str = Depends(authenticate)):
        from .templates import delete_template

        return delete_template(template_id)

    # ── Signatures ────────────────────────────────────────────────────────────

    @app.get("/api/signatures")
    async def signature_get(service: str = "default", _user: str = Depends(authenticate)):
        from .signatures import get_signature

        return get_signature(service)

    @app.put("/api/signatures/{service}")
    async def signature_set(
        service: str,
        payload: dict[str, Any] = Body(...),
        _user: str = Depends(authenticate),
    ):
        from .signatures import set_signature

        return set_signature(service, payload.get("signature", ""))

    @app.delete("/api/signatures/{service}")
    async def signature_delete(service: str, _user: str = Depends(authenticate)):
        from .signatures import delete_signature

        return delete_signature(service)

    # ── Scheduled Send ────────────────────────────────────────────────────────

    @app.post("/api/schedule")
    async def schedule_create(
        payload: dict[str, Any] = Body(...),
        _user: str = Depends(authenticate),
    ):
        from .scheduler import schedule_send, start_scheduler

        to = payload.get("to", "").strip()
        subject = payload.get("subject", "").strip()
        body = payload.get("body", "").strip()
        send_at = payload.get("send_at", 0)
        if not to or not subject or not body or not send_at:
            raise HTTPException(status_code=422, detail="to, subject, body, and send_at are required")
        result = schedule_send(to, subject, body, send_at, payload.get("service", "default"))
        start_scheduler(mcp_app)
        return result

    @app.get("/api/schedule")
    async def schedule_list(_user: str = Depends(authenticate)):
        from .scheduler import list_scheduled

        return {"scheduled": list_scheduled()}

    @app.delete("/api/schedule/{scheduled_id}")
    async def schedule_cancel(scheduled_id: str, _user: str = Depends(authenticate)):
        from .scheduler import cancel_scheduled

        return cancel_scheduled(scheduled_id)

    # ── Skills ───────────────────────────────────────────────────────────────

    @app.get("/api/skills")
    async def list_skills(_user: str = Depends(authenticate)):
        resources = await mcp_app.list_resources()
        skills: list[dict[str, str]] = []
        for r in resources:
            uri = getattr(r, "uri", None) or str(getattr(r, "name", ""))
            if uri.startswith("skill://") and "/SKILL.md" in uri:
                name = uri.replace("skill://", "").split("/")[0]
                skills.append({"name": name, "uri": uri})
        return {"skills": skills}

    @app.get("/api/skills/{name}")
    async def get_skill_content(name: str, _user: str = Depends(authenticate)):
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
        except Exception as exc:
            raise HTTPException(status_code=404, detail=f"Skill not found: {name}") from exc

    # ── Local LLM autodiscovery ───────────────────────────────────────────────

    @app.get("/api/llm/models")
    async def get_llm_models(_user: str = Depends(authenticate)):
        providers: list[dict[str, Any]] = []

        async with httpx.AsyncClient(timeout=3.0) as client:
            # Try localhost and 127.0.0.1 (Windows Ollama compat)
            ollama_ok = False
            for host in ("http://localhost:11434", "http://127.0.0.1:11434"):
                try:
                    r = await client.get(f"{host}/api/tags")
                    if r.status_code == 200:
                        data = r.json()
                        models = [m["name"] for m in data.get("models", [])]
                        providers.append(
                            {
                                "id": "ollama",
                                "name": "Ollama",
                                "endpoint": f"{host}/v1/chat/completions",
                                "available": True,
                                "models": models,
                            }
                        )
                        ollama_ok = True
                        break
                except Exception:
                    continue

            if not ollama_ok:
                providers.append(
                    {
                        "id": "ollama",
                        "name": "Ollama",
                        "endpoint": "http://localhost:11434/v1/chat/completions",
                        "available": False,
                        "models": [],
                    }
                )

            try:
                r = await client.get("http://localhost:1234/v1/models")
                if r.status_code == 200:
                    data = r.json()
                    models = [m["id"] for m in data.get("data", [])]
                    providers.append(
                        {
                            "id": "lmstudio",
                            "name": "LM Studio",
                            "endpoint": "http://localhost:1234/v1/chat/completions",
                            "available": True,
                            "models": models,
                        }
                    )
            except Exception:
                providers.append(
                    {
                        "id": "lmstudio",
                        "name": "LM Studio",
                        "endpoint": "http://localhost:1234/v1/chat/completions",
                        "available": False,
                        "models": [],
                    }
                )

        for cloud in [
            {
                "id": "anthropic",
                "name": "Anthropic (Claude)",
                "models": ["claude-sonnet-4-20250514", "claude-opus-4-20250514", "claude-haiku-4-5-20251001"],
            },
            {"id": "openai", "name": "OpenAI", "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]},
            {
                "id": "google",
                "name": "Google Gemini",
                "models": ["gemini-2.0-flash", "gemini-2.5-pro", "gemini-2.0-flash-lite"],
            },
        ]:
            providers.append({**cloud, "endpoint": None, "available": None})

        return {"providers": providers}

    @app.post("/api/llm/configure")
    async def configure_llm(
        payload: dict[str, Any] = Body(...),
        _user: str = Depends(authenticate),
    ):
        provider = payload.get("provider", "ollama")
        model = payload.get("model", "")
        endpoint = payload.get("endpoint", "")
        if provider == "ollama":
            os.environ["AI_PROVIDER"] = "ollama"
            os.environ["AI_MODEL"] = model
            if endpoint:
                os.environ["AI_ENDPOINT"] = endpoint
        elif provider in ("anthropic", "openai", "google", "lmstudio"):
            os.environ["AI_PROVIDER"] = provider
            os.environ["AI_MODEL"] = model
            if endpoint:
                os.environ["AI_ENDPOINT"] = endpoint
            if payload.get("api_key"):
                key_env = {
                    "anthropic": "ANTHROPIC_API_KEY",
                    "openai": "OPENAI_API_KEY",
                    "google": "GOOGLE_API_KEY",
                }.get(provider)
                if key_env:
                    os.environ[key_env] = payload["api_key"]

        ai_router.provider = os.environ.get("AI_PROVIDER", "ollama")
        ai_router.model = os.environ.get("AI_MODEL", "")
        ai_router.endpoint = os.environ.get("AI_ENDPOINT", "")

        return {"success": True, "provider": provider, "model": model}

    # ── Chat ─────────────────────────────────────────────────────────────────

    @app.post("/api/chat")
    async def chat(
        payload: dict[str, Any] = Body(...),
        _user: str = Depends(authenticate),
    ):
        query = payload.get("query", "").strip()
        if not query:
            raise HTTPException(status_code=422, detail="query is required")
        response = await ai_router.route_query(query)
        return {"response": response}

    @app.post("/api/parse-config")
    async def parse_config(
        payload: dict[str, Any] = Body(...),
        _user: str = Depends(authenticate),
    ):
        description = payload.get("description", "").strip()
        service_type = payload.get("service_type", "smtp")
        fields = payload.get("fields", [])
        if not description:
            raise HTTPException(status_code=422, detail="description is required")
        query = (
            f"Based on this description, return ONLY valid JSON with the config fields filled in:\n\n"
            f"Description: {description}\n\n"
            f"Service type: {service_type}\n"
            f"Available fields: {', '.join(fields)}\n\n"
            f"Return ONLY the JSON object."
        )
        response = await ai_router.route_json_query(query)
        return {"success": True, "response": response}

    # ── Text improvement (LLM-assisted writing) ──────────────────────────────

    @app.post("/api/improve")
    async def improve_text(
        payload: dict[str, Any] = Body(...),
        _user: str = Depends(authenticate),
    ):
        text = payload.get("text", "").strip()
        if not text:
            raise HTTPException(status_code=422, detail="text is required")
        style = payload.get("style", "professional")
        length = payload.get("length", "same")
        mood = payload.get("mood", "neutral")
        response = await ai_router.improve_text(text, style, length, mood)
        return {"success": True, "response": response}

    @app.post("/api/expand")
    async def expand_text(
        payload: dict[str, Any] = Body(...),
        _user: str = Depends(authenticate),
    ):
        """Expand a short note into a full email with creative fictional details."""
        text = payload.get("text", "").strip()
        if not text:
            raise HTTPException(status_code=422, detail="text is required")
        style = payload.get("style", "humorous")
        length = payload.get("length", "long")
        context = payload.get("context", "none")
        context_hints = {
            "venice": "Set the scene in Venice during the Biennale. Mention sinking palazzos, overpriced spritzes, a gondolier who quotes Deleuze, and an installation made of 4000 humming Roomba vacuums.",
            "mars": "Set the scene on Elon Musk's Mars colony. Mention the unreliable oxygen recycler, the 'everything is fine' facade, the HOA fees for the geodesic dome, and the local café that only serves protein slurry.",
            "castle": "Set the scene in a medieval castle. Mention drafty corridors, a jester who gives bad financial advice, a dragon in the moat, and the annual 'tRounament of Self-Actualization'.",
            "underwater": "Set the scene in an underwater research base. Mention the leaky porthole, the chef who only serves kelp, a strangely intelligent octopus roommate, and the daily 'shark drill'.",
            "space": "Set the scene on a space station. Mention the zero-gravity coffee spills, the annoying AI voice, the cargo bay full of IKEA flatpacks, and the guy from accounting who keeps trying to open the airlock.",
            "wildwest": "Set the scene in a Wild West frontier town. Mention the tumbleweeds in the saloon, the sheriff who's also the baker, a horse that gives legal advice, and the annual 'High Noon Haggling Championship'.",
        }
        hint = context_hints.get(context, "")
        query = f"Expand this short note into a full email. Make it {style} and {length}. Weave in creative, humorous fictional details. {hint}\n\nNote: {text}\n\nReturn ONLY the expanded email, no explanations."
        response = await ai_router.route_query(query)
        return {"success": True, "response": response, "context": context}

    # ── Service types reference ──────────────────────────────────────────────

    @app.get("/api/service-types")
    async def get_service_types(_user: str = Depends(authenticate)):
        return {
            "types": {
                "smtp": {
                    "label": "SMTP / IMAP",
                    "fields": [
                        "smtp_server",
                        "smtp_port",
                        "smtp_user",
                        "smtp_password",
                        "smtp_from",
                        "imap_server",
                        "imap_port",
                        "imap_user",
                        "imap_password",
                    ],
                    "required": ["smtp_server", "smtp_user", "smtp_password"],
                },
                "api": {
                    "label": "Transactional API (SendGrid, Mailgun, Resend)",
                    "fields": ["api_key", "api_url", "from_email", "service_type"],
                    "required": ["api_key", "api_url", "from_email"],
                },
                "local": {
                    "label": "Local Testing (MailHog, Mailpit)",
                    "fields": ["smtp_server", "smtp_port", "http_url", "service_type"],
                    "required": ["smtp_server"],
                },
                "webhook": {
                    "label": "Webhook (Slack, Discord)",
                    "fields": ["webhook_url", "service_type"],
                    "required": ["webhook_url"],
                },
            }
        }

    # ── MailLab (throwaway SMTP server) ─────────────────────────────────────

    @app.post("/api/lab/start")
    async def lab_start(_user: str = Depends(authenticate)):
        """Start a throwaway SMTP server for testing."""
        from .lab import start_server

        return start_server()

    @app.post("/api/lab/stop")
    async def lab_stop(_user: str = Depends(authenticate)):
        """Stop the throwaway SMTP server."""
        from .lab import stop_server

        return stop_server()

    @app.get("/api/lab/status")
    async def lab_status(_user: str = Depends(authenticate)):
        """Get throwaway server status and email count."""
        from .lab import server_status

        return server_status()

    @app.get("/api/lab/emails")
    async def lab_list_emails(_user: str = Depends(authenticate)):
        """List captured emails from the throwaway server."""
        from .lab import list_emails

        emails = list_emails()
        return {"emails": emails, "count": len(emails)}

    @app.get("/api/lab/emails/{email_id}")
    async def lab_get_email(email_id: str, _user: str = Depends(authenticate)):
        """Get full detail of a captured email."""
        from .lab import get_email

        email = get_email(email_id)
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        return email

    @app.delete("/api/lab/emails")
    async def lab_clear_emails(_user: str = Depends(authenticate)):
        """Clear all captured emails."""
        from .lab import clear_emails

        return clear_emails()

    @app.post("/api/lab/inject")
    async def lab_inject_email(
        payload: dict[str, Any] = Body(...),
        _user: str = Depends(authenticate),
    ):
        """Inject a synthetic email into the captured store."""
        from .lab import inject_email

        result = inject_email(
            payload.get("from", "sender@test.com"),
            payload.get("to", ["recipient@test.com"]),
            payload.get("subject", "Test"),
            payload.get("body", ""),
            payload.get("html"),
        )
        return {"success": True, "email": result}

    @app.post("/api/lab/generate")
    async def lab_generate_emails(
        payload: dict[str, Any] = Body(...),
        _user: str = Depends(authenticate),
    ):
        """Generate AI-crafted test emails and inject them into the lab."""
        count = min(payload.get("count", 5), 25)
        scenario = payload.get("scenario", "general")
        from .lab import inject_email

        prompt = (
            f"Generate {count} realistic test emails for the scenario '{scenario}'. "
            "Return ONLY valid JSON as an array of objects, each with: "
            "from (email), to (array of emails), subject, body (plain text). "
            "Make them realistic: varied senders, timestamps implied in the body, "
            "and scenario-appropriate content. "
            "No markdown, no code fences, no explanations — just the JSON array."
        )
        response = await ai_router.route_json_query(prompt)
        import json as _json

        try:
            cleaned = response.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            messages = _json.loads(cleaned)
        except Exception:
            return {"success": False, "error": "AI did not return valid JSON", "raw": response[:500]}

        if not isinstance(messages, list):
            messages = [messages]
        injected = []
        for msg in messages[:count]:
            entry = inject_email(
                msg.get("from", "ai@generator.local"),
                msg.get("to", ["inbox@lab.local"]),
                msg.get("subject", "(No Subject)"),
                msg.get("body", ""),
            )
            injected.append(entry)
        return {"success": True, "injected": len(injected), "emails": injected}

    @app.post("/api/lab/forward/{email_id}")
    async def lab_forward_email(
        email_id: str,
        payload: dict[str, Any] = Body(...),
        _user: str = Depends(authenticate),
    ):
        """Forward a captured lab email to a real email address."""
        from .lab import get_email

        email = get_email(email_id)
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        target = payload.get("to", "").strip()
        if not target:
            raise HTTPException(status_code=422, detail="'to' is required")
        result = await mcp_app.call_tool(
            "send_email",
            {
                "to": target,
                "subject": f"Fwd: {email['subject']}",
                "body": f"--- Forwarded from MailLab ---\n\nFrom: {email['from']}\n\n{email['text_body']}",
                "service": payload.get("service", "default"),
            },
        )
        return _extract_tool_result(result)

    # ── Creative Workflows ────────────────────────────────────────────────────

    WORKFLOWS: dict[str, str] = {
        "love-letter": ("Write a love letter. Make it {tone} and {mood}. The recipient is my {recipient}. Sign it with love. Output format: {fmt_text}"),
        "breakup": ("Write a breakup email to my {recipient}. Make it {tone} and {mood}. Output format: {fmt_text}"),
        "thank-you": ("Write a warm thank-you note to my {recipient}. Make it {tone}. Output format: {fmt_text}"),
        "complaint": ("Write a {mood} complaint letter to my {recipient}. Make it {tone}. Output format: {fmt_text}"),
        "apology": ("Write an apology email to my {recipient}. Make it {tone}. Output format: {fmt_text}"),
        "fan-mail": ("Write an enthusiastic fan letter to my {recipient}. Make it {tone}. Mention something you admire. Output format: {fmt_text}"),
        "hate-mail": ("Write a hilariously passive-aggressive email to my {recipient}. Make it comedic and over-the-top, not actually mean. Tone: {tone}. Output format: {fmt_text}"),
    }

    FORMAT_INSTRUCTIONS: dict[str, str] = {
        "text": "Return ONLY the email body as plain text.",
        "ascii": "Include a large ASCII art illustration at the top. Use chars like @ # % * / \\ | ( ) - + = . Make it impressive.",
        "svg": "Return an inline SVG document wrapped in ```svg ... ``` that renders the email as a decorative card, max 800x600, then the text below.",
    }

    @app.post("/api/workflow")
    async def run_workflow(
        payload: dict[str, Any] = Body(...),
        _user: str = Depends(authenticate),
    ):
        workflow = payload.get("workflow", "").strip()
        if workflow not in WORKFLOWS:
            raise HTTPException(status_code=422, detail=f"Unknown workflow '{workflow}'. Available: {list(WORKFLOWS.keys())}")
        template = WORKFLOWS[workflow]
        tone = payload.get("tone", "sincere")
        mood = payload.get("mood", "warm")
        recipient = payload.get("recipient", "beloved")
        fmt = payload.get("format", "text")
        fmt_text = FORMAT_INSTRUCTIONS.get(fmt, FORMAT_INSTRUCTIONS["text"])
        query = template.format(recipient=recipient, tone=tone, mood=mood, fmt_text=fmt_text)
        response = await ai_router.route_query(query)
        return {"success": True, "workflow": workflow, "response": response, "format": fmt}

    # ── Mail Watcher (background IMAP polling) ─────────────────────────────

    @app.post("/api/watcher/start")
    async def watcher_start(
        payload: dict[str, Any] = Body(...),
        _user: str = Depends(authenticate),
    ):
        from .watcher import start_watcher

        interval_s = max(30, min(payload.get("interval", 60), 3600))
        webhook_url = payload.get("webhook_url", "").strip()
        services = payload.get("services", [{"name": "default", "folder": "INBOX"}])
        return start_watcher(interval_s, webhook_url, services, mcp_app)

    @app.post("/api/watcher/stop")
    async def watcher_stop(_user: str = Depends(authenticate)):
        from .watcher import stop_watcher

        return stop_watcher()

    @app.get("/api/watcher/status")
    async def watcher_status(_user: str = Depends(authenticate)):
        from .watcher import watcher_status

        return watcher_status()

    @app.post("/api/check-spam")
    async def check_spam(
        payload: dict[str, Any] = Body(...),
        _user: str = Depends(authenticate),
    ):
        """Check if an email looks like spam based on content analysis."""
        from .autorespond import is_spam

        return is_spam(payload)

    # ── Auto-Respond ─────────────────────────────────────────────────────────

    @app.get("/api/auto-rules")
    async def auto_list_rules(_user: str = Depends(authenticate)):
        from .autorespond import list_rules

        return {"rules": list_rules()}

    @app.post("/api/auto-rules")
    async def auto_add_rule(
        payload: dict[str, Any] = Body(...),
        _user: str = Depends(authenticate),
    ):
        from .autorespond import add_rule

        name = payload.get("name", "").strip()
        match_pattern = payload.get("match_pattern", "").strip()
        if not name or not match_pattern:
            raise HTTPException(status_code=422, detail="name and match_pattern are required")
        return add_rule(
            name=name,
            match_field=payload.get("match_field", "subject"),
            match_pattern=match_pattern,
            reply_body=payload.get("reply_body", ""),
            reply_subject=payload.get("reply_subject", ""),
            use_ai=payload.get("use_ai", False),
            auto_send=payload.get("auto_send", False),
            ai_prompt=payload.get("ai_prompt", ""),
            service=payload.get("service", "default"),
        )

    @app.put("/api/auto-rules/{rule_id}")
    async def auto_update_rule(
        rule_id: str,
        payload: dict[str, Any] = Body(...),
        _user: str = Depends(authenticate),
    ):
        from .autorespond import update_rule

        return update_rule(rule_id, payload)

    @app.delete("/api/auto-rules/{rule_id}")
    async def auto_delete_rule(rule_id: str, _user: str = Depends(authenticate)):
        from .autorespond import delete_rule

        return delete_rule(rule_id)

    @app.get("/api/auto-pending")
    async def auto_list_pending(_user: str = Depends(authenticate)):
        from .autorespond import list_pending

        return {"pending": list_pending()}

    @app.post("/api/auto-pending/{pending_id}/approve")
    async def auto_approve_pending(pending_id: str, _user: str = Depends(authenticate)):
        from .autorespond import approve_pending

        result = approve_pending(pending_id)
        if result["success"]:
            pend = result["pending"]
            svc = pend.get("service", "default")
            result2 = _extract_tool_result(
                await mcp_app.call_tool(
                    "send_email",
                    {
                        "to": pend.get("email_from", ""),
                        "subject": pend.get("reply_subject", ""),
                        "body": pend.get("reply_body", ""),
                        "service": svc,
                    },
                )
            )
            if result2.get("success"):
                result["sent"] = True
                result["send_message"] = "Reply sent"
            else:
                result["sent"] = False
                result["send_message"] = result2.get("error", "Send failed")
        return result

    @app.post("/api/auto-pending/{pending_id}/reject")
    async def auto_reject_pending(pending_id: str, _user: str = Depends(authenticate)):
        from .autorespond import reject_pending

        return reject_pending(pending_id)

    @app.post("/api/auto-respond")
    async def auto_respond_now(
        payload: dict[str, Any] = Body(...),
        _user: str = Depends(authenticate),
    ):
        email_id = payload.get("email_id", "").strip()
        service = payload.get("service", "default")
        folder = payload.get("folder", "INBOX")
        if not email_id:
            raise HTTPException(status_code=422, detail="email_id is required")
        result = _extract_tool_result(await mcp_app.call_tool("fetch_email_detail", {"email_id": email_id, "service": service, "folder": folder}))
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=f"Email {email_id} not found")
        from .autorespond import add_pending, match_rule

        rule = match_rule(result)
        if not rule:
            return {"success": True, "matched": False, "message": "No rule matched"}
        prompt = rule.get("ai_prompt", "") or f"Write a friendly reply to this email.\n\nFrom: {result.get('from', '')}\nSubject: {result.get('subject', '')}\nBody: {result.get('text_body', '')[:2000]}"
        reply_body = await ai_router.route_query(prompt)
        reply_subject = f"Re: {result.get('subject', '')}"
        entry = add_pending(result, reply_body, reply_subject, rule["id"], service)
        return {"success": True, "matched": True, "rule": rule["name"], "queued": True, "pending_id": entry["id"]}
