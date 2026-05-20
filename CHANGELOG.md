# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **New MCP Tools**: `fetch_email_detail`, `delete_email`, `mark_email_read`, `search_emails`, `remove_service` (total: 14 tools)
- **REST API endpoints**: email detail (`GET /api/inbox/{id}`), mark-read/unread, delete, full-text search (`/api/search`), draft CRUD (`/api/drafts`), service CRUD (`POST/PUT/DELETE /api/services/{name}`), service types reference (`/api/service-types`)
- **Draft management**: save/load/delete drafts persisted to JSON file, auto-delete draft on send
- **Email Detail view** (`/email`): full email reader with HTML body rendering, reply/forward links, delete/mark-read actions
- **Search page** (`/search`): full-text IMAP search with results linking to detail view
- **Services page** (`/services`): form-based service configuration (no JSON textarea), AI Assist with 9 provider presets (Gmail, Outlook, Yahoo, ProtonMail, MailHog, SendGrid, Mailgun, Slack, Discord), password fields with show/hide toggle, live test/delete
- **Toast notification system**: context-based success/error/info toasts with auto-dismiss
- **AI Improve in Compose**: style/length/mood selectors (6 each), calls `/api/improve` to rewrite email body via LLM
- **Settings page**: email service credentials form (SMTP/IMAP user/pwd entry with save/test)
- **Prompt injection defense**: `src/email_mcp/sanitize.py` with 37 zero-width/bidi Unicode character stripping + safety boundary wrapping (`<<< UNTRUSTED EXTERNAL DATA >>>` preamble) applied to all MCP tool returns, 5 service files, 6 test fixtures, 27 tests
- **Live topbar health check**: polls `/api/status` every 30s, shows green/red status dot
- **Auto-refresh inbox**: 30s polling with toggle
- **Docs restructure**: 8 sub-readmes in `docs/` (gmail, outlook, protonmail, api-services, local-testing, webhook-integrations, configuration, safety-hardening); short user-facing README cut from 514â†’110 lines
- **Tabbed Help page**: Quick Start, Email Systems, Configuration, Tools, Safety, SOTA tabs
- **Functional Tools page**: Execute buttons now call real REST endpoints with per-tool result display
- **Fixed dashboard**: real stats (unread count, connected services, drafts), clickable recent activity
- **Uvicorn log spam suppression**: access/error loggers set to WARNING in server lifespan

### Changed
- Updated version to 0.4.0
- `manifest.json` and `mcpb.json` updated with new tools and version
- Inbox now clickable â†’ navigates to email detail, inline delete button on hover
- Compose now supports BCC, HTML toggle, draft save/load panel
- Sidebar: added Search and Services nav items
- Dashboard: removed fake "system load = tools_count * 4" stat, shows real draft count

### Security
- **Prompt injection hardening**: two-layer defense (Unicode stripping + safety boundary wrapping) applied to check_inbox, fetch_email_detail, search_emails, mailing_list_latest tool returns
- FastMCP `instructions` declares safety posture up front

## [0.4.1] - 2026-05-19

### Added
- **Tauri 2.0 native desktop wrapper** (
ative/): single-window app using system WebView2, no Electron/Chromium
  - System tray icon with minimize-to-tray support
  - Auto-launches PyInstaller sidecar backend on startup; kills it cleanly on exit
  - Emits ackend-status events (eady / error) to the frontend via Tauri IPC
- **PyInstaller sidecar build** (email-mcp-backend.spec, 
ative/build-sidecar.ps1):
  - Single-file EXE (one-file mode, no one-dir COLLECT) for Tauri externalBin compatibility
  - Copies output to 
ative/binaries/email-mcp-backend-x86_64-pc-windows-msvc.exe
  - Expanded hiddenimports: full uvicorn protocol/lifespan tree + all email_mcp.* submodules
  - pathex = ["src"] so imports resolve correctly inside the frozen bundle
- **
ative/package.json**: pins @tauri-apps/cli ^2 so 
px resolves locally instead of fetching on every run
- **justfile** — new targets in Native (Tauri) section:
  - uild-sidecar: run PyInstaller, copy binary to 
ative/binaries/
  - uild-all: uild-sidecar then uild-native in one step
  - 	auri-dev: hot-reload dev mode (backend must be running separately)
  - uild-native / uild-native-debug: run 
pm install before Tauri CLI

### Fixed
- **
ative/main.rs**: uvicorn readiness detection now checks both CommandEvent::Stdout and CommandEvent::Stderr — uvicorn's startup message (Uvicorn running on ...) is emitted via Python logging to stderr, so the previous stdout-only check never fired

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

