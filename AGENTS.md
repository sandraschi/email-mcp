# AGENTS.md — Session Context

## 2026-05-14: Major webapp overhaul + safety hardening (COMPLETED)

### What was done (full session summary)

**Backend** (server.py + web.py):
- Added 5 new MCP tools: `fetch_email_detail`, `delete_email`, `mark_email_read`, `search_emails`, `remove_service`
- Added service methods: `fetch_message()`, `delete_message()`, `mark_read()` on SMTPEmailService with full IMAP implementations
- Added 10+ REST endpoints: email detail, search, drafts CRUD, service CRUD, service-types reference, text improvement
- Uvicorn access log suppression (set uvicorn loggers to WARNING in lifespan)

**Frontend** (webapp/):
- **New pages**: email detail view (`/email`), search (`/search`), services management (`/services`) with AI Assist presets
- **New system**: toast notifications (`components/toast.tsx`)
- **Inbox overhaul**: click-to-read, inline delete, 30s auto-refresh toggle, search shortcut
- **Compose overhaul**: draft save/load/delete panel, HTML toggle, BCC, AI Improve (style/length/mood selectors)
- **Tools page**: all Execute buttons functional with per-tool result display
- **Dashboard**: real stats (no fakes), draft count, clickable recent activity, auto-refresh
- **Topbar**: live backend health check (polls `/api/status` every 30s)
- **Settings**: email service credentials form (SMTP/IMAP user/pwd) + existing AI config
- **Sidebar**: added Search and Services nav items
- **Help**: rewritten with 6 tabs (Quick Start, Email Systems, Configuration, Tools, Safety, SOTA)

**Documentation**:
- README cut from 514→110 lines
- `docs/` directory with 8 sub-readmes: quickstart, gmail, outlook, protonmail, api-services, local-testing, webhook-integrations, configuration, safety-hardening

**Safety Hardening**:
- Created `sanitize.py` with two-layer prompt injection defense
- Layer 1: 37 zero-width/bidi Unicode characters stripped at service layer
- Layer 2: Safety boundary wrapping (`<<< UNTRUSTED EXTERNAL DATA >>>` + preamble) at MCP tool return boundary
- Applied to: check_inbox, fetch_email_detail, search_emails, mailing_list_latest
- FastMCP instructions hardened with safety declaration
- 6 test fixtures in `tests/fixtures/` (direct_command, unicode_hidden, bidi_override, misspelled_bypass, context_collapse, mixed)
- 27 tests in `tests/test_sanitize.py` — all pass

**Config files updated**: CHANGELOG.md, manifest.json (0.4.0, 15 tools), mcpb.json (0.4.0), README.md

### Key patterns
- Prompt injection defense: `<<< UNTRUSTED EXTERNAL DATA | EMAIL {source} >>>` prefix + `---BEGIN/END---` delimiters
- FastMCP tool registration: all tools in `EmailMCP._register_tools()` via `@self.mcp.tool()` decorator
- REST endpoints in web.py delegate via `mcp_app.call_tool()`
- Toast system: context-based in `components/toast.tsx`, `useToast()` hook
- Ports: 10812 frontend, 10813 backend

### Startup
```powershell
.\start.ps1  # Backend + frontend
```

### Tests
```powershell
uv run --extra test pytest tests/test_sanitize.py -v  # 27 safety tests
```
