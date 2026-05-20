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
