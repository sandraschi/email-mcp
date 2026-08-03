# BUILD_LOG.md — email-mcp NSIS builds

## 2026-08-03 — v0.5.0-beta.2 (second certified build, refreshed)

**Result**: PASS — CUA 8/8. Rebuilt after installed-app verification fixes:

| # | Symptom | Root cause | Fix |
|---|---------|------------|-----|
| 8 | Installed app: "Graph not authorized" after OAuth consent | Graph service derived its account from the seeded `.env` placeholder (`you@example.com`); token stored under the real account | `oauth.graph_account()` + lazy `_account()` resolution in GraphEmailService; default-service fallback also triggers on placeholder SMTP configs |
| 9 | Installed app: tokens/rules lost | defaults pointed into the frozen temp dir | Tauri mode (`EMAIL_MCP_TAURI=1`) stores OAuth tokens + rules in `%LOCALAPPDATA%\ai.fleet.email-mcp\`; first run seeds `.env` from the bundled example |

**Verified installed-app flow**: install → `.env` seeded → OAuth consent → token in LOCALAPPDATA → `send_email(service="default")` via Graph.

## 2026-08-03 — v0.5.0-beta.1 (first certified build)

**Result**: PASS — `just cua-nsis-test` 8/8 phases (install → launch → window → screenshot → 15-page nav walk → diagnostics → uninstall).

Installer: `native/target/release/bundle/nsis/Email MCP_0.5.0-beta.1_x64-setup.exe` (~30 MB).

### Issues hit and fixes (all committed)

| # | Symptom | Root cause | Fix |
|---|---------|------------|-----|
| 1 | `PyInstaller failed (exit 1)` — `PackageNotFoundError: fastmcp` | `build-sidecar.ps1` ran `uv run pyinstaller` → isolated uv **tool** env (py3.13, no project packages) | Install PyInstaller into the project venv (`uv add --dev pyinstaller`) and invoke `.venv\Scripts\pyinstaller.exe` |
| 2 | `resource path 'resources\email-mcp-backend.exe' doesn't exist` | sidecar script only copied to `binaries/` (dev triple name), not `resources/` | Copy exe to `native/resources/` at build time (build.ps1 does this; keep in sync) |
| 3 | `resource path 'resources\.env.example' doesn't exist` | tauri.conf listed `.env.example` but nothing copied it | build.ps1 now copies `.env.example` (was bundling the real `.env` — credentials leak, now fixed) |
| 4 | `resource path '..\scripts\install-mcp-clients.ps1' doesn't exist` | dead reference, hooks.nsh never used it | Removed from tauri.conf resources |
| 5 | Frozen exe ran **stdio** despite `MCP_PORT` | `run_server.py` never translated env → HTTP mode | Dual-transport entry per fleet standard: overwrite `sys.argv` with `--http --host --port` before `main()` |
| 6 | CUA "Backend not reachable" (401/404) | `/api/v1/health` required Basic auth (probe sends none); dev uvicorn also held port 10813 | `/api/v1/health` + `/api/v1/diagnostics` made public (fleet smoke surface); free port before CUA run |
| 7 | CUA kill phase missed dev uvicorn | kill-by-name only | Operator-side note: stop dev stack (`start.ps1` Ctrl+C) before `just cua-nsis-test` |

### Gates
- Backend exe: 27.6 MB (≥5 MB gate) ✓
- Installer: 29.9 MB (≥1 MB gate) ✓
- Frozen exe smoke: HTTP mode + `/api/v1/health` + `/api/v1/diagnostics` 200, 44 tools ✓
- CUA nav walk: distinct per-page screenshots ✓
