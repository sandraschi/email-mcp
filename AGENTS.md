# AGENTS.md -- Session Context

## Repo: email-mcp

Full-featured email server for MCP clients. Web dashboard at 10812, backend at 10813. 86 tests, 0 ruff warnings. 32+ MCP tools.

---

## Key Architecture

| Layer | Tech | Notes |
|-------|------|-------|
| MCP Framework | FastMCP 3.2+ | `fastmcp>=3.2.0,<4` |
| Web Framework | FastAPI | REST endpoints in web.py |
| Frontend | React 19 + Vite + Tailwind | Port 10812 |
| Tests | pytest (69) + Playwright (17) | 86 total |
| SMTP Testing | aiosmtpd 1.4+ | Throwaway servers for testing |
| DB | JSON file storage | Contacts, drafts, rules, pending |

### Critical Gotcha

`mcp_app.call_tool()` returns `CallToolResult` objects in FastMCP 3.2, not raw dicts. Always use `_extract_tool_result()` when calling tools from web.py REST endpoints. See `web.py` for the helper.

---

## Current State (2026-05-23)

### Features
- **32+ MCP tools**: send, receive, search, delete, mark-read/unread, folders CRUD, list/configure/remove services, mailing lists, email_help, suggest_subject, agentic_assist, watcher, contacts, workflows, auto-respond
- **Auto-Respond**: rule engine + AI drafting + pending queue + spam spoof mode (irate/mock-stupid/absurd/polite-but-confused)
- **Bulk Send**: paste email lists, max 50, anti-spam warnings
- **Mail Watcher**: background IMAP polling with webhook POST
- **Mail Lab**: throwaway aiosmtpd SMTP server with AI message generator
- **Contacts**: full CRUD + CSV/vCard/Google People/Microsoft Graph import + curated public official lists (US Congress, Austrian Parliament, EU Commission)
- **Creative Workflows**: 7 AI presets (love letter, complaint, etc.) with text/ascii/svg output
- **Expander**: short-note-to-full-email with 6 fictional contexts
- **Quick Setup**: 8 providers (Gmail/Outlook/Yahoo/iCloud/ProtonMail/Zoho/GMX/Fastmail)
- **Prompt injection defense**: 37 Unicode chars stripped + safety boundary wrapping
- **Folder CRUD**: list/create/delete/rename IMAP folders
- **justfile**: SOTA standard (inline dashboard, build=uv sync, check=fmt+lint, ci pipeline)

### Sidebar Pages
Dashboard `/`, Inbox `/inbox`, Email Detail `/email`, Compose `/compose` (with AI Improve, Expander, Bulk Send), Search `/search`, AI Chat `/chat` (with creative workflows), Mail Lab `/lab` (with watcher), Services `/services`, Contacts `/contacts` (with curated lists), Auto-Reply `/auto-respond` (rules + pending), Tools `/tools`, Settings `/settings`, Help `/help` (6 tabs)

### Key Files Created This Session
| File | Purpose |
|------|---------|
| `src/email_mcp/autorespond.py` | Rule engine, spam detection, spoof mode |
| `src/email_mcp/curated_lists.py` | Public official contact lists |
| `src/email_mcp/contacts.py` | Contact CRUD + multi-source import |
| `src/email_mcp/watcher.py` | Background IMAP polling |
| `src/email_mcp/lab.py` | Throwaway SMTP server manager |
| `webapp/src/pages/auto-respond.tsx` | Auto-respond management UI |
| `webapp/src/pages/contacts.tsx` | Contact management UI |
| `webapp/src/pages/lab.tsx` | Mail Lab UI |
| `webapp/e2e/email-mcp.spec.ts` | 17 Playwright e2e tests |
| `webapp/playwright.config.ts` | Playwright config |

### Key Patterns
- REST endpoints in web.py delegate via `mcp_app.call_tool()` + `_extract_tool_result()`
- Contact import via CSV, vCard, Google People API, Microsoft Graph API
- Auto-respond rules stored in `autorespond_rules.json`, pending in `autorespond_pending.json`
- Watcher uses asyncio background task, polls IMAP, POSTs webhook on new mail
- Spam detection uses 10 regex groups, spoof generates AI replies in 4 tones

### Startup
```powershell
.\start.ps1  # Backend + frontend
just lab      # CLI throwaway SMTP
```

### Tests
```powershell
.venv\Scripts\pytest.exe tests/ -q                          # 69 backend tests
cd webapp && npx playwright test && cd ..                    # 17 Playwright tests
# Full suite: .venv\Scripts\pytest.exe tests/ -q && cd webapp && npx playwright test && cd ..
```

### Ports
- 10812: Vite frontend
- 10813: FastAPI backend + MCP HTTP

Install docs: follow mcp-central-docs/standards/AGENT_INSTALL_REFERENCE.md
