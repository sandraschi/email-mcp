
## [0.5.0-beta.1] - 2026-08-03 "Graph API + Fleet Connectors" (beta)

### Highlights
- **Microsoft Graph service** — send/receive for personal Outlook/Hotmail
  (basic SMTP auth disabled on those accounts): OAuth device flow with
  Microsoft's public client ID (no Azure registration), auto-refreshing tokens,
  `service="default"` auto-backs onto Graph when a token exists.
- **Fleet connectors** — `email_connector` tool + REST: aiwatcher fleet ingest,
  robofang email hook, connector health (opt-in, fail-soft).
- **Folder treeview** in the webapp Inbox (unread badges, expandable, inline CRUD)
  + custom folder name -> Graph id resolution.
- **New email ops**: `copy_email`, `forward_email` (tools + REST + webapp).
- **Fixes**: 202-empty-body Graph send crash; OAuth token refresh kept the wrong
  scope family (expired tokens now refresh correctly); `.env` now loaded at startup.
- 189 tests passing, 42 MCP tools.

## [Unreleased] -- 2026-06-14

### Added (2026-08-03 - Graph send/receive + connectors)
- **Microsoft Graph service**: personal Outlook/Hotmail accounts have SMTP/IMAP basic
  auth disabled (535 5.7.139) — the `graph` service (and `service="default"` when an
  OAuth token exists for an Outlook-family account) now sends/receives via the Graph
  REST API (`POST /me/sendMail`). OAuth uses Microsoft's public Graph CLI client ID —
  no Azure app registration needed (`EMAIL_MCP_OAUTH_CLIENT_ID`).
- **OAuth device flow fixes** (oauth.py): scopes now include `openid profile email`
  (Microsoft returns no `id_token` otherwise and valid tokens were discarded); account
  extraction falls back to the access_token JWT.
- **Graph send fix** (graph_service.py): `/me/sendMail` returns 202 with an empty body —
  `_request()` crashed on `resp.json()` (`Expecting value: line 1 column 1`); empty 2xx
  bodies now handled.
- **`.env` loading**: server.py now loads the repo `.env` (nothing did before — config
  never reached the server when launched via start.ps1/uvicorn).
- **Folder name resolution** (graph_service.py): custom folders (e.g. `Github`,
  `Family/Dog`) resolve displayName -> Graph folder id (folder names 400 in Graph URLs);
  `list_folders` returns a full tree with unread/total counts (recursive childFolders).
- **Webapp folder treeview**: Inbox page now has a sidebar folder tree (expandable,
  unread badges, per-folder icons) replacing the flat dropdown, plus folder CRUD
  (new/rename/delete) directly in the tree.
- **Email ops**: `copy_email` and `forward_email` tools + REST (`POST /api/inbox/{id}/copy`,
  `/api/inbox/{id}/forward`); Graph + IMAP implementations; email-detail page gained
  working Move/Copy (folder picker) and Forward (to + comment) actions.
- **Fleet connectors**: `email_connector` MCP tool + REST (`GET /api/connectors/status`,
  `POST /api/connectors/aiwatcher`, `POST /api/connectors/robofang`) push events to
  aiwatcher's `/api/fleet/ingest` and robofang's `/api/hooks/email` (opt-in via
  `EMAIL_MCP_AIWATCHER_URL` / `EMAIL_MCP_ROBOFANG_URL`, fail-soft).
- **Tests**: 188 passing (9 connector tests, 4 Graph copy/forward tests).

### Fixed (2026-07-31 - assfix)
- Packaging: rebuilt `mcpb/src` staging as `mcpb/src/email_mcp/` (was flattened bare modules — bundle could not import itself); purged `.pyc` dross
- Packaging: MCPB prompts brought to 3-4-100 bar (system.md 3000 words, user.md 4000 words, examples.json 104 entries)
- Packaging: `.mcpbignore` now excludes webapp/, mcpb/, logs/, monitoring/, reports/, data/, examples/, *.bak (previous pack was 46 MB of bloat)
- Manifest: root + mcpb manifest.json tool lists regenerated to the actual 39 registered tools
- Docs: added docs/DEVELOPMENT.md, docs/TOOLS.md, docs/TROUBLESHOOTING.md
- Webapp: data-testid sweep across 13 pages (page container + key controls)
- Webapp: fixed production build (tsc -b) type errors in chat.tsx, compose.tsx, inbox.tsx, settings.tsx, tools.tsx, contacts.tsx
- Webapp: dashboard font/contrast fixes (status labels to text-sm text-slate-300)
- Tests: pytest.ini enforces coverage floor (--cov=email_mcp --cov-fail-under=30, current 39.8%)
- Hygiene: removed stale .bak files; glama.json tool count corrected 32 -> 39

### Fixed (2026-07-24 - assfix)
- CORS: replaced `allow_origins=["*"]` with fleet-standard explicit origins + `allow_origin_regex` for Tailscale/LAN
- CORS: replaced `run_http_async()` in transport.py with `uvicorn.Server` on `mcp.http_app()` with CORS middleware
- Imports: added missing `imaplib`, `email`, `asyncio` imports in tool_registry.py (search_emails was broken)
- Imports: added `from email.header import decode_header` in email_services.py
- Imports: added `decode_email_header`, `sanitize_text`, `wrap_untrusted_list`, `load_mailing_list_entries` imports in tool_registry.py
- Imports: fixed E402 (module-level import not at top) in server.py
- Tool: added `email_shutdown` self-termination tool
- Service: added `attachments` parameter to LocalEmailService, APIEmailService, WebhookEmailService for interface parity
- Test: fixed test_e2e_real.py (LocalEmailService.send_email arg count mismatch)

### Added
- `.env.example` — service config template
- `.claude-plugin/hooks/hooks.json` — Claude Code SessionStart hook
- `.windsurfrules` — Windsurf session context
- `.github/copilot-instructions.md` — GitHub Copilot tool awareness
- `.opencode/skills/email-mcp/SKILL.md` — OpenCode session context
- `.pre-commit-config.yaml` — Ruff pre-commit hooks
- `webapp/bun.lock` — Bun lockfile per fleet standard

### Added
- Tauri CORS: 	auri://localhost, http://tauri.localhost, https://tauri.localhost in CORS origins
- Tauri CORS: _TAURI env var toggle with llow_origin_regex for secure WebView access
- build.ps1: auto-copy NSIS installer to dist/ on build
- CUA-NSIS: config-driven smoke test (`scripts/cua-smoke.py`, `scripts/cua-nsis-config.json`)
- CUA-NSIS: `just build-native` + `just cua-nsis-test` recipes
- CUA-NSIS: 11-phase smoke (install, launch, WebView OCR, feature route, diagnostics, uninstall)
- CUA-NSIS: local certification -- all 11 phases pass locally (2026-06-14)

### Changed
- CORS: llow_origins=["*"] → explicit origins list for Tauri webview compatibility
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Auto-Respond system**: rule engine with regex matching (subject/from/body), AI drafting, pending queue for human approval, auto-send
- **Spam detection**: 10 pattern groups, `POST /api/check-spam` endpoint
- **Spoof mode**: hilarious AI-generated replies to scammers -- 4 tones (irate, mock-stupid, absurd, polite-but-confused)
- **Bulk send**: paste email lists, max 50/batch, CAN-SPAM/GDPR warnings, consent checkbox
- **Curated public lists**: US Congress (10), Austrian Parliament (7), EU Commission (3) -- importable to contacts with one click
- **Mail Watcher**: background IMAP polling with webhook notifications (`start_watcher`, `stop_watcher`, `watcher_status` MCP tools)
- **Contact import**: Google People API, Microsoft Graph API (OAuth token-based), plus full CRUD + CSV/vCard import
- **Folder CRUD**: list, create, delete, rename IMAP folders (MCP tools + REST + frontend)
- **Quick Setup**: 8 provider presets (Gmail/Outlook/Yahoo/iCloud/ProtonMail/Zoho/GMX/Fastmail) -- one-click with email+password
- **Creative Workflows**: 7 presets (love-letter, breakup, thank-you, complaint, apology, fan-mail, hate-mail) with text/ascii/svg format
- **Expander**: short-note-to-full-email with 6 context scenarios (Venice Biennale, Mars Colony, Medieval Castle, etc.)
- **Playwright e2e tests**: 17 tests covering dashboard, inbox, compose, services, settings, chat, lab, contacts, help, sidebar, REST API
- **MCP tools**: `start_watcher`, `stop_watcher`, `watcher_status`, `add_contact`, `search_contacts`, `run_workflow`, `add_auto_rule`, `list_auto_rules`, `delete_auto_rule`, `list_pending_replies`, `approve_reply`, `auto_respond_now`

### Changed
- justfile aligned with SOTA standards: inline dashboard, `build=uv sync`, `check=fmt+lint`, `ci` pipeline
- Updated version to 0.4.1 across all files
- `ruff` moved from production deps to dev deps (pyproject.toml)
- Removed stale `[tool.black]` config (project uses ruff format)
- `tools_exposed` now reports 15 tools (was hardcoded to 6)
- `email_help` tool listing now includes all 15 tools
- `update_service` endpoint properly extracts call_tool result for error handling
- MailLab email count endpoint uses clean `len(emails)` instead of `__import__` hack
- Cleaned 16 stale `.bak` files from codebase
- Leftover debug logging in `decode_email_header` removed

### Fixed
- README no longer references non-existent `just bootstrap` / `just serve` recipes
- Settings page correctly filters embedding models from LM Studio model list
- Test Connection button now actually tests the selected provider (not the stale backend default)

## [0.4.0] - 2026-05-14

### Added
- **New MCP Tools**: `fetch_email_detail`, `delete_email`, `mark_email_read`, `search_emails`, `remove_service` (total: 15 tools)
- **REST API endpoints**: email detail, mark-read/unread, delete, full-text search, draft CRUD, service CRUD, service types reference
- **Draft management**: save/load/delete drafts persisted to JSON file, auto-delete draft on send
- **Email Detail view** (`/email`): full email reader with HTML body rendering
- **Search page** (`/search`): full-text IMAP search
- **Services page** (`/services`): form-based config with AI Assist presets
- **Toast notification system**: context-based success/error/info toasts
- **AI Improve in Compose**: style/length/mood selectors for LLM rewriting
- **Settings page**: email service credentials form
- **Prompt injection defense**: 37 Unicode chars stripped + safety boundary wrapping, 6 test fixtures, 27 tests
- **Live topbar health check**: polls `/api/status` every 30s
- **Auto-refresh inbox**: 30s polling with toggle
- **Docs restructure**: 8 sub-readmes in `docs/`
- **Tabbed Help page**: 6 tabs including Safety
- **Functional Tools page**: execute buttons call real REST endpoints
- **Mail Lab** (`/lab`): throwaway SMTP server (aiosmtpd) + AI message generator
- **Uvicorn log spam suppression**

### Changed
- Updated version to 0.4.0
- Inbox clickable, inline delete, auto-refresh
- Compose: BCC, HTML toggle, drafts
- Sidebar: Search and Services nav items
- Dashboard: real stats, draft count
- Chat page: loads SKILL.md, shows provider info
- All `call_tool` results now properly extracted via `_extract_tool_result()`

### Security
- Two-layer prompt injection defense: Unicode stripping + safety boundary wrapping

## [0.4.1] - 2026-05-19

### Added
- **Tauri 2.0 native desktop wrapper** (`native/`): single-window app using system WebView2
  - System tray icon with minimize-to-tray support
  - Auto-launches PyInstaller sidecar backend on startup; kills it cleanly on exit
  - Emits `backend-status` events (ready / error) to the frontend via Tauri IPC
- **PyInstaller sidecar build** (`native/build-sidecar.ps1`):
  - Single-file EXE for Tauri externalBin compatibility
  - Copies output to `native/binaries/email-mcp-backend-x86_64-pc-windows-msvc.exe`
  - Expanded hidden imports: full uvicorn protocol/lifespan tree + all `email_mcp.*` submodules
- **`native/package.json`**: pins `@tauri-apps/cli` ^2 so `npx` resolves locally
- **justfile**: new targets for Tauri build, debug, dev mode
- **`mailing_list_latest` tool**: now correctly handles invalid IDs and missing service configs
  - uild-sidecar: run PyInstaller, copy binary to
ative/binaries/
  - uild-all: uild-sidecar then uild-native in one step
  - 	auri-dev: hot-reload dev mode (backend must be running separately)
  - uild-native / uild-native-debug: run
pm install before Tauri CLI

### Fixed
- **
ative/main.rs**: uvicorn readiness detection now checks both CommandEvent::Stdout and CommandEvent::Stderr -- uvicorn's startup message (Uvicorn running on ...) is emitted via Python logging to stderr, so the previous stdout-only check never fired

## [0.3.1] - 2026-03-20

### Added
- **Mailing list presets**: `EMAIL_MCP_MAILING_LISTS` / `EMAIL_MCP_MAILING_LISTS_FILE` (JSON), tools `mailing_lists_catalog`, `mailing_list_latest`; optional `from_contains` / `subject_contains` on `check_inbox` (IMAP + local MailHog/Mailpit).
- **`src/email_mcp/mailing_lists.py`** â€” Pydantic-validated list entries.
- **`justfile`** â€” `sync`, `copy-mcp`, `lint`, `fmt`, `test`, `check`, `run`.
- **`copy_server.py`** â€” Syncs `server.py`, `mailing_lists.py`, and `skills/` into `mcp-server/src/email_mcp/`.

### Changed
- **`glama.json` / `manifest.json`**: version **0.3.1**, tool count **10**; sampling + prompts + skills documented in Glama capabilities.
- **`pytest.ini`**: `[pytest]` section, `asyncio_mode = auto` (for pytest-asyncio).

### Notes
- **Sampling / agentic / prompts / skills**: unchanged â€” `suggest_email_subject`, `email_agentic_assist`, prompts, `email_mcp/skills/` remain optional UX helpers (not required for core SMTP/IMAP).

## [0.3.0] - 2026-01-17

### Added
- **FastMCP 2.14.3 Standards Compliance**: Updated to latest FastMCP protocol version
- **Conversational Tool Returns**: All tools now return natural language messages alongside structured data
- **Zed Extension Support**: Added extension.toml configuration for Zed editor integration
- **Enhanced MCPB Packaging**: Updated manifest and packaging for modern MCP clients

### Changed
- Updated all tool responses to include conversational `message` fields for better user experience
- Professionalized README and documentation without marketing language
- Updated version numbers across all configuration files (manifest.json, glama.json, extension.toml)

### Technical
- Upgraded FastMCP dependency to >=2.14.3,<3.0.0
- Added conversational messaging to send_email, check_inbox, and configure_service tools
- Updated server version strings to 0.3.0
- Enhanced error messages with contextual information
- Maintained backward compatibility with existing configurations

## [0.2.2] - 2026-01-13

### Added
- **Server-to-Server Communication**: Leverages FastMCP 2.14.1 capabilities for direct MCP server collaboration
- **AI Email Collaboration**: Email MCP can now communicate with local-llm-mcp for intelligent email processing
- **ProtonMail Documentation**: Comprehensive setup guide for both free (Bridge) and paid (direct) accounts
- **Enhanced AI Features**: Direct server communication enables advanced AI email workflows

### Fixed
- **Email Header Decoding**: Fixed borked/encoded email headers in inbox results
- Properly decode UTF-8 Base64 and Quoted-Printable encoded subject lines and sender names
- All email headers now display in readable format instead of encoded strings

### Technical
- Added `decode_email_header()` function using Python's `email.header.decode_header()`
- Enhanced IMAP inbox checking to decode RFC 2047 encoded headers
- FastMCP 2.14.1 server communication framework for cross-server collaboration
- Maintains backward compatibility with all email service types

## [0.2.1] - 2026-01-12

### Added
- AI Email Management Orchestrator - Server composition of minimail-mcp + local-llm-mcp
- `weed_trash` tool - AI-powered email cleanup and filtering
- `email_summarizer` tool - Smart inbox summaries grouped by topic and sender
- `smart_email_filter` tool - AI-generated email filtering rules
- Server composition architecture using FastMCP `mount()` for cross-server workflows
- Test framework for validating compositing functionality
- Safety-first design with `dry_run` modes for all destructive operations

### Changed
- Updated version to 0.2.1 to reflect new AI capabilities
- Enhanced README with orchestrator quick start and feature overview

### Technical
- Implemented FastMCP server composition patterns
- Created modular orchestrator architecture with clean separation of concerns
- Added cross-server tool calling capabilities
- Established AI email management as a new category of MCP applications

## [0.2.0] - 2026-01-12

### Added
- MCPB packaging support for Claude Desktop
- Complete manifest.json with tool definitions
- Glama integration with enhanced glama.json
- CI/CD pipeline with GitHub Actions
- Health monitoring and metrics collection system
- Comprehensive testing framework
- Code quality enforcement (Ruff, MyPy)
- Professional documentation and examples
- Monitoring stack with health checks and performance tracking

### Changed
- Updated project structure to src/ layout
- Enhanced README with standards compliance information
- Improved configuration management
- Updated version to reflect SOTA compliance

### Technical
- Added extensive prompt templates for Claude Desktop
- Implemented monitoring stack (health_check.py, metrics.py, config.py)
- Added comprehensive glama.json configuration
- Created CI/CD workflow with multi-version Python testing
- Established professional development standards

## [0.1.0] - 2026-01-01

### Added
- Initial multi-service email platform
- SMTP/IMAP support for standard providers
- Basic service configuration
- Core email sending and receiving functionality
- Async operations support
