# AGENTS.md -- Session Context

## Repo: email-mcp

Full-featured email server for MCP clients. Web dashboard at 10812, backend at 10813.
188 tests, 42 MCP tools. Microsoft Graph support for personal Outlook/Hotmail
(basic SMTP auth is disabled on those accounts — 535 5.7.139).

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

## Current State (2026-08-03)

### Features
- **45+ MCP tools**: send, receive, search, delete, move, copy, forward, mark-read/unread, folders CRUD, list/configure/remove services, mailing lists, email_help, suggest_subject, agentic_assist, watcher, contacts, workflows, auto-respond, email_connector, **email_rag**, **sync_email_rag**, **email_rag_stats**
- **Neural Email RAG & Vector Store**: Local LanceDB vector repository (`data/email_lancedb`) with FastEmbed 384-dim semantic embeddings (`BAAI/bge-small-en-v1.5`), GPU accelerator auto-discovery (`RAG_GPU=1` / `CUDAExecutionProvider`), paragraph-aware chunking with email header context injection, and incremental sync skips
- **Standardized RAG Operations REST**: Non-blocking asynchronous background sweep worker (`POST /api/rag/sweep`, `GET /api/rag/status/{job_id}`, `GET /api/rag/stats`, `GET /api/rag/search`, with `/api/reindex` backward compatibility)
- **Microsoft Graph**: personal Outlook/Hotmail via Graph REST (send/receive/search/folders); OAuth device flow with public client ID (no Azure registration); `service="default"` auto-backs onto Graph when a token exists for an Outlook account
- **Folder treeview**: Inbox sidebar tree (expandable, unread badges, icons) + inline folder CRUD (new/rename/delete); custom folder names resolve to Graph folder ids
- **Fleet connectors**: `email_connector` tool + REST — aiwatcher fleet ingest and robofang email hook (opt-in env, fail-soft)
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
Dashboard `/`, Inbox `/inbox`, Email Detail `/email`, Compose `/compose` (with AI Improve, Expander, Bulk Send), Search `/search` (with Neural RAG vs IMAP mode switch), RAG Operations `/rag` (KPI metrics, live running progress, and test console), AI Chat `/chat` (with creative workflows), Mail Lab `/lab` (with watcher), Services `/services`, Contacts `/contacts` (with curated lists), Auto-Reply `/auto-respond` (rules + pending), Tools `/tools`, Settings `/settings`, Help `/help` (6 tabs)

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

<!-- FLEET-CONTEXT:BEGIN (generated by fleet-gate/agent_context.py) -->
## Fleet context — required reading

**Before any task in this fleet, read
`mcp-central-docs/standards/AGENT_READING_ORDER.md`.** It carries the AGENTS.md chain,
the 13-file Primary Read List, the domain read list, the pitfalls docs and the bug
depot. There are 124 files under `standards/`; that file is the index that makes them
usable.

Search `mcp-central-docs/troubleshooting/BUGS_DEPOT.md` by symptom *before* debugging
anything — a bug the fleet has already paid for is a lookup, not an investigation.

These few are repeated here rather than linked, because a rule whose violation produces
**no error** cannot depend on anyone following a link:

- **Never author multi-line file content with a Bash heredoc** (`cat > file <<'EOF'`) —
  it intermittently writes nothing on this Windows/Git-Bash setup. Use the Write tool.
  (BUG-031)
- **Never patch files with inline Python** (`python - <<'PY'`, `python -c`) — Python's
  string parser silently converts backslash escapes, so `"D:\Dev\repos\x"` becomes
  `D:` + `\D` + `ev` + CR + `epos` + CR + `x`. One observed case deleted dict entries
  while staying valid Python with a clean lint. Use Edit and Write. (BUG-039)
- **Never hardcode a port.** Claim one with `mcp-central-docs/fleet-gate/claim_ports.py`,
  which checks `operations/WEBAPP_PORTS.md` *and* every `fleet-start.config.ps1`.
- **Max 5 files per commit and per script invocation**; 3+ file edits need a timestamped
  `.bak` per file written first.
- **Never restart an NSSM service by killing its child** — `sc.exe stop/start`, then
  verify a NEW PID owns the port.
- **Never invent a date or location**; read the clock or write `UNKNOWN-DATE`.
- **Prove changes by running them.** A gate that reports success having examined nothing
  is this fleet's most common failure mode.
<!-- FLEET-CONTEXT:END -->
