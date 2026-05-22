set windows-shell := ["pwsh.exe", "-NoLogo", "-Command"]

# Open the interactive recipe dashboard in the browser
default:
    @pwsh.exe -NoProfile -ExecutionPolicy Bypass -File ../mcp-central-docs/scripts/just-dashboard.ps1 -Path .

# ── Quality ───────────────────────────────────────────────────────────────────

# Execute Ruff SOTA v13.1 linting
lint:
    Set-Location '{{justfile_directory()}}'
    uv run ruff check .
    Set-Location '{{justfile_directory()}}\webapp'
    npx @biomejs/biome ci .

# Execute Ruff SOTA v13.1 fix and formatting
fix:
    Set-Location '{{justfile_directory()}}'
    uv run ruff check . --fix --unsafe-fixes
    uv run ruff format .
    Set-Location '{{justfile_directory()}}\webapp'
    npx @biomejs/biome check --write .

# ── Hardening ─────────────────────────────────────────────────────────────────

# Execute Bandit security audit
check-sec:
    Set-Location '{{justfile_directory()}}'
    uv run bandit -r src/

# Execute safety audit of dependencies
audit-deps:
    Set-Location '{{justfile_directory()}}'
    uv run safety check

# ── Dev ───────────────────────────────────────────────────────────────────────

# Repo statistics (Markdown, tools, FastMCP, MCP tools)
stats:
    Set-Location '{{justfile_directory()}}'
    uv run python tools/repo_stats.py

# Install dev deps (pytest, ruff) via uv
sync:
    uv sync --extra test --extra dev

# Copy src/email_mcp → mcp-server/src/email_mcp (server, mailing_lists, skills)
copy-mcp:
    uv run python copy_server.py

# Format
fmt:
    uv run ruff format src tests

# Unit tests (no network)
test:
    uv run --extra test pytest tests -q

# Lint + test (CI-ish)
check: lint test

# Run MCP server (stdio)
run:
    uv run python -m email_mcp.server

# ── Native (Tauri) ────────────────────────────────────────────────────────────

# Build PyInstaller sidecar binary → native/binaries/
build-sidecar:
    Set-Location '{{justfile_directory()}}'
    pwsh -NoLogo -File '{{justfile_directory()}}\native\build-sidecar.ps1'

# Build Tauri desktop app — sidecar must exist first (run build-sidecar)
build-native:
    Set-Location '{{justfile_directory()}}\native'
    $env:Path = "$env:USERPROFILE\.cargo\bin;$env:Path"
    npm install
    npx @tauri-apps/cli build

# Build sidecar then full Tauri release in one step
build-all: build-sidecar build-native

# Build Tauri app in debug mode (faster rebuild, devtools on)
build-native-debug:
    Set-Location '{{justfile_directory()}}\native'
    $env:Path = "$env:USERPROFILE\.cargo\bin;$env:Path"
    npm install
    npx @tauri-apps/cli build --debug

# Run Tauri in hot-reload dev mode (backend must already be running)
tauri-dev:
    Set-Location '{{justfile_directory()}}\native'
    $env:Path = "$env:USERPROFILE\.cargo\bin;$env:Path"
    npm install
    npx @tauri-apps/cli dev

# Install Tauri CLI locally (pinned via native/package.json)
tauri-cli:
    Set-Location '{{justfile_directory()}}\native'
    npm install

# ── Convenience ────────────────────────────────────────────────────────────────

# Bootstrap: install all dependencies (test + dev extras)
bootstrap:
    Set-Location '{{justfile_directory()}}'
    uv sync --extra test --extra dev

# Start web dashboard (backend + frontend)
serve dev:
    Set-Location '{{justfile_directory()}}'
    .\start.ps1

# Build MCPB package
build:
    Set-Location '{{justfile_directory()}}'
    uv run python build_mcpb.py

# Launch throwaway MailLab SMTP server on a free port
lab:
    uv run python -c "
from email_mcp.lab import start_server, stop_server, server_status, list_emails
import time
s = start_server()
print(f'Lab SMTP server running on 127.0.0.1:{s[\"port\"]}')
print('Press Ctrl+C to stop')
try:
    while True:
        st = server_status()
        print(f'  [{time.strftime(\"%H:%M:%S\")}] {st[\"email_count\"]} emails captured')
        time.sleep(5)
except KeyboardInterrupt:
    stop_server()
    print('Server stopped')
"

# Clean build artifacts and backups
clean:
    Set-Location '{{justfile_directory()}}'
    -Remove-Item -Recurse -Force build/, dist/, target/, .coverage, *.bak, *.spec 2>$null
    -Remove-Item -Recurse -Force src/**/*.bak, src/**/*.spec, webapp/**/*.bak 2>$null
    Get-ChildItem -Recurse -Filter __pycache__ | Remove-Item -Recurse -Force 2>$null
    Write-Host 'Cleaned'
