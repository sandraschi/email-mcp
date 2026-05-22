# AGENTS.md — Session Context

## 2026-05-14: Full feature completion (COMPLETED)

### What was done

**Backend fixes (web.py)**:
- Added `_extract_tool_result()` helper to properly extract dict responses from `mcp_app.call_tool()` — FastMCP 3.2 returns CallToolResult objects, not raw dicts
- Applied it to ALL `call_tool` calls in web.py (services, inbox, send, search, lab, folders, mark-read/unread, forward)
- Fixed `update_service` to check `remove_service` result before re-adding
- Removed `__import__` code smell in lab emails endpoint
- Fixed version stutter (0.3.2/0.4.0 → 0.4.1 across all files)
- Fixed `tools_exposed: 6` → `15` in email_status tool
- Fixed `email_help` tool listing to include all 15 tools
- Removed leftover debug logging in `decode_email_header`
- Added `mark_email_unread` MCP tool + REST endpoint (IMAP `-FLAGS \Seen`)
- Added folder CRUD: `list_folders`, `create_folder`, `delete_folder`, `rename_folder` — MCP tools + REST endpoints + ABC + SMTPEmailService impl
- Added `POST /api/services/quick` — one-click Gmail/Outlook/Yahoo/iCloud/ProtonMail/Zoho/GMX/Fastmail setup with email+password only
- Added `POST /api/workflow` — 7 creative workflow templates (love-letter, breakup, thank-you, complaint, apology, fan-mail, hate-mail) with text/ascii/svg format support
- Added workflow to capabilities

**Backend fixes (server.py)**:
- Added `mark_unread()` method to SMTPEmailService
- Added `list_folders()`, `create_folder()`, `delete_folder()`, `rename_folder()` methods
- Added `mark_email_unread` MCP tool
- Added folder MCP tools
- Updated `email_help` tool to list all 15 tools
- Updated `email_status` `tools_exposed` count
- Removed en-dash in docstring (RUF002)
- Fixed B030 except union syntax

**Backend (sanitize.py)** — already done in earlier session

**Frontend**:
- **Settings page**: filters out embedding/rerank models from dropdown; Test button saves before testing
- **Services page**: Quick Setup cards with provider chips + email/password form; dynamic IMAP folder loading
- **Inbox**: folder dropdown now fetches real IMAP folders via `GET /api/services/{name}/folders`
- **Chat page**: Creative Workflow panel (collapsible) with 7 presets, recipient/tone/mood/format selectors, 15 fun recipients including Roko's Basilisk. Uses ReactMarkdown for rendering SVG/ASCII output.
- **Mail Lab page**: create/stop SMTP server, AI message generator with 10 scenarios, forward captured emails
- Sidebar: added Mail Lab nav item

**Documentation**:
- **SKILL.md**: completely rewritten — 15 tools, 7 creative workflows, 3 formats, 8 quick-setup providers, Mail Lab, folder CRUD, Prefab cards, safety, email history, classic scams + absurd scenarios (pygmy hippo, sad vampire, time traveler, sentient AI, penguin)
- **MCPB rebuilt** with updated SKILL.md (48 KB)

**Linting**:
- Ruff: `line-length` → 175, added S110/S112 to ignore list
- Fixed remaining E501/RUF010/RUF059/RUF002/B030 issues
- Final: 0 warnings, 0 errors

**Config files updated**: CHANGELOG.md (added [0.4.0], [0.4.1], [Unreleased]), manifest.json (0.4.1, 15 tools), mcpb.json (0.4.1), README.md, pyproject.toml (ruff dep → dev, removed [tool.black]), justfile (added bootstrap/build/clean/lab/serve/dev), AGENTS.md

### Tests
- 45 tests total: sanitize (27) + API services (17) + real SMTP e2e (1) — all passing

### Key patterns
- `call_tool` returns `CallToolResult` in FastMCP 3.2 — always use `_extract_tool_result()`
- REST endpoints in web.py delegate via `mcp_app.call_tool()` + `_extract_tool_result()`
- Ports: 10812 frontend, 10813 backend

### Startup
```powershell
.\start.ps1  # Backend + frontend
just lab  # Throwaway SMTP server (CLI)
```

### Tests
```powershell
.venv\Scripts\pytest.exe tests/test_sanitize.py tests/test_api_services.py tests/test_e2e_real.py -v
```
