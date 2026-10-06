# BUILD_LOG.md — email-mcp NSIS builds

## 2026-10-07 — v0.6.0 (PASS after 3 pre-build fixes + 1 build regression caught)

Installer: `native/target/release/bundle/nsis/Email MCP_0.6.0_x64-setup.exe` (49.6 MB), backend
sidecar 44.8 MB, plus `dist/email-mcp-v0.6.0.mcpb` (127 KB). Built from a clean git worktree of the
release branch (the working tree held unrelated uncommitted work); the worktree folder must be
named exactly `email-mcp` because `native/build.ps1` derives the spec name from the folder name.
CUA-NSIS smoke: **12/12 phases passed** on the final build. Nav OCR misses on AI Chat, Auto-Reply,
Help (template text drift, same as earlier builds) and Settings (the screenshot shows Windows'
Task View overlay covering the screen, an automation artifact, not the app).
Re-checked after every install/uninstall cycle: the NSSM `email-mcp` service kept the same PID and
answered health 200 on 10813.

Pre-build audit (TAURI_PRODUCTION_PITFALLS Phase 1) found and fixed:

1. **Side-by-side rule (A).** The shell's `BACKEND_PORT` was 10813, the dev backend AND the live
   NSSM `email-mcp` service port, and `free_port` was a blind `Get-NetTCPConnection | taskkill` of
   whatever owned it: launching the installed app would have killed the service. Claimed
   `email-mcp-native` 11251/11252 (`claim_ports.py`); `BACKEND_PORT` 11252, CSP and the
   build-time `VITE_API_BASE` follow; `free_port` is now image-scoped, never kills its own PID or
   an unknown port owner (pitfalls 14/15).
2. **Frontend hardcoded the dev port.** `webapp/src/lib/api.ts` ignored `VITE_API_BASE`, so the
   installed UI would have called the service, not its sidecar. Env-driven now.
3. **`run_server.py` taskkilled anything on dev frontend port 10812 at startup**, including when
   the desktop app spawned it. Skipped under `EMAIL_MCP_TAURI`.
4. `main.rs` reaped the sidecar on `Exit` only; now `ExitRequested` too (G).

Build regression caught by checking sizes, not by a test:

5. **The first 0.6.0 build was 200 MB (backend 197 MB).** After the RAG backend merge,
   `email_mcp.server` imports the RAG tools lazily inside a function, which PyInstaller follows;
   a venv re-sync had put lancedb/pyarrow/onnxruntime in, so ~580 MB uncompressed (lancedb 311 MB)
   was frozen into the sidecar, against the decision to ship RAG off in the installer. Fix:
   explicit `excludes` in `email-mcp-backend.spec` (lancedb, lance, pyarrow, fastembed,
   onnxruntime, tokenizers, huggingface_hub, hf_xet) and a >120 MB gate in `native/build.ps1`.
   Rebuilt: backend 44.8 MB. Verified by running the frozen exe itself: health 200, real port
   reported, log line `Email RAG tools disabled (optional dependency missing) - No module named
   'lancedb'`. (An earlier claim that the mcpb pack check proved this was wrong: that venv had
   lancedb installed.)

Process notes: `pack.ps1` runs `uv` without `UV_NO_SYNC` and re-syncs the venv, so run the NSIS
build with `UV_NO_SYNC=1` or the build depends on venv state. `uv.lock` was stale against
`pyproject.toml` at v0.5.1 (refreshed in this release). The pytest suite rewrites the tracked
`src/drafts.json` / `src/signatures.json`; revert them before committing.

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
