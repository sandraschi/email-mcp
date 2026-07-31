# Development

## Stack

| Layer | Tech | Notes |
|-------|------|-------|
| MCP framework | FastMCP >=3.4.4 | Tools registered in `src/email_mcp/tools/tool_registry.py` |
| Web framework | FastAPI | REST surface in `src/email_mcp/web.py`, CORS in `server.py` + `transport.py` |
| Frontend | React 19 + Vite + Tailwind | `webapp/`, port 10812 (dev), proxies `/api` and `/mcp` to 10813 |
| Tests | pytest (148) + Playwright (17) | `tests/`, `webapp/e2e/` |
| SMTP testing | aiosmtpd | Mail Lab + MailHog services |
| Packaging | uv + hatchling | `uv.lock` committed; MCPB via `just mcpb-pack`; Tauri NSIS via `just build-native` |

## Repo layout

```
src/email_mcp/
├── server.py           # EmailMCP server class, FastAPI app, CORS, main()
├── transport.py        # stdio/http/sse transport, MCP HTTP endpoint + CORS
├── web.py              # REST endpoints for the dashboard
├── tools/
│   ├── tool_registry.py  # ALL 39 MCP tools (single registration point)
│   └── contacts.py       # contact store operations
├── services/email_services.py  # SMTP/API/local/webhook service classes
├── sanitize.py         # prompt-injection defense + error_response helper
├── mailing_lists.py    # EMAIL_MCP_MAILING_LISTS presets
├── autorespond.py      # rule engine + spam classifier
├── watcher.py          # background IMAP polling
├── lab.py              # throwaway aiosmtpd servers
├── ai.py               # LLM/sampling helpers (improve, expand, subjects)
├── workflows.py        # creative workflow presets
├── templates.py        # template store
├── signatures.py       # signature store
└── scheduler.py        # scheduling helpers
```

## Commands

```powershell
uv sync --extra test --extra dev   # install
just lint                          # ruff + biome
just fmt                           # ruff format
just test                          # pytest + playwright
just serve                         # start backend + frontend
just mcpb-pack                     # build .mcpb bundle
just build-native                  # PyInstaller sidecar + Tauri NSIS
just cua-nsis-test                 # install/launch/verify/uninstall smoke test
```

## Key patterns

- **REST delegates to MCP**: `web.py` calls `mcp_app.call_tool()` and extracts the
  result with `_extract_tool_result()` — FastMCP 3.x returns `CallToolResult`, not
  raw dicts. Do not call service internals from web routes.
- **Registering a tool**: add a `@mcp.tool(annotations=...)` function inside
  `register_tools()` in `tool_registry.py`. Every tool returns `{success, message,
  ...}`; failures include `error` and use `error_response()` from `sanitize.py`
  (auto-logs with `logger.exception`).
- **Safety wrapping**: receiving paths wrap email content with
  `wrap_untrusted_dict` / `wrap_untrusted_list`; `sanitize_text` strips 37
  injection Unicode chars.
- **Services**: implement the `EmailService` interface (send_email, check_inbox,
  ...) in `services/email_services.py`; register factory entries for new
  providers.
- **Prompt-injection defense**: never concatenate raw email content into prompts
  without sanitizing first.

## Tests

```powershell
uv run pytest tests/ -q                    # 148 tests
cd webapp; npx playwright test             # 17 e2e tests
```

New tools need a test in `tests/` mirroring the return-shape contract. Coverage
floor: 30% (pytest.ini) — raise it as coverage grows; the gap is web.py +
transport.py, which are REST/transport plumbing.

## Version bump

1. `pyproject.toml` version
2. `manifest.json` + `mcpb/manifest.json` (run the manifest-fix script or the tool
   enumeration snippet in `scripts/`)
3. `glama.json` version + tool count
4. `CHANGELOG.md` entry
5. `tauri.conf.json` version (native/)
