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

## 2026-05-23: Auto-Respond, Bulk Send, Spam/Spoof, Curated Lists (COMPLETED)

### What was done
- **Auto-Respond system** (`src/email_mcp/autorespond.py`): rule engine with regex matching, AI drafting via LLM, pending queue, approve/reject, auto-send. 6 MCP tools + REST endpoints + /auto-respond frontend page (Rules tab + Pending tab)
- **Spam detection**: 10 pattern groups (Nigerian prince, crypto, viagra, phishing, etc.), `is_spam()` function, `POST /api/check-spam` endpoint
- **Spoof mode**: 4 AI reply tones (irate, mock-stupid, absurd, polite-but-confused) for hilarious auto-replies to scammers. Spoof rules auto-send by default
- **Bulk send**: `POST /api/send-bulk`, max 50 recipients, CAN-SPAM/GDPR warning text, explicit consent checkbox for >10 recipients. Frontend section on Compose page
- **Curated public lists** (`src/email_mcp/curated_lists.py`): US Congress (10), Austrian Parliament (7), EU Commission (3), test civic (3). Collapsible section on Contacts page, one-click import to contacts
- **Contacts**: Google People API + Microsoft Graph API import (OAuth token-based)
- **Folder CRUD**: list/create/delete/rename IMAP folders (MCP tools + REST + frontend)
- **Quick Setup**: 8 provider presets (Gmail/Outlook/Yahoo/iCloud/ProtonMail/Zoho/GMX/Fastmail)
- **Creative Workflows**: 7 AI letter presets, text/ascii/svg format
- **Expander**: short-note-to-full-email with 6 fictional context scenarios
- **Mail Watcher**: background IMAP polling with webhook POST, frontend controls on Mail Lab page
- **Playwright e2e tests**: 17 tests covering all pages + 7 REST endpoints
- **justfile**: aligned with SOTA standards (inline dashboard, build=uv sync, check=fmt+lint, ci pipeline)
- **README**: hero rewrite, quick start cleanup, test badge, full feature list
- **protonmail.md**: complete rewrite with Gmail comparison, pros/cons, CERN/Swiss background
- **api-services.md**: clarified transactional email (not spam cannons), comparison table
- **playwright_e2e_sota.md**: new fleet standard in mcp-central-docs
- **Changelog**: comprehensive unreleased entries

### Key files created
- `src/email_mcp/autorespond.py` — rule engine + spam detection + spoof mode
- `src/email_mcp/curated_lists.py` — curated public official lists
- `src/email_mcp/contacts.py` — contact CRUD + CSV/vCard/Google/Microsoft import
- `src/email_mcp/watcher.py` — background IMAP polling
- `webapp/src/pages/auto-respond.tsx` — auto-respond management page
- `webapp/src/pages/contacts.tsx` — contact management page
- `webapp/e2e/email-mcp.spec.ts` — 17 Playwright tests
- `webapp/playwright.config.ts` — Playwright config

### Stats
- 86 total tests: 27 sanitize + 17 API services + 16 contacts + 5 mailing lists + 2 connection + 1 e2e real SMTP + 17 Playwright
- Ruff: 0 warnings
- Python: 3.12+, FastMCP 3.2+, aiosmtpd 1.4+

### Ports
- 10812 frontend, 10813 backend
