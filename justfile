set windows-shell := ["powershell.exe", "-NoProfile", "-Command"]
import 'scripts/just/fleet.just'

# -- Dashboard ------------------------------------------------------------------

# Display SOTA Industrial Dashboard
default:
    @just --list

# -- Quality -------------------------------------------------------------------

# Execute Ruff SOTA v13.1 linting
lint:
    Set-Location '{{justfile_directory()}}'
    uv run ruff check .
    Set-Location '{{justfile_directory()}}\webapp'
    npx @biomejs/biome ci .

# Format code with Ruff
fmt:
    uv run ruff format src tests

# Execute Ruff SOTA v13.1 fix and formatting
fix:
    Set-Location '{{justfile_directory()}}'
    uv run ruff check . --fix --unsafe-fixes
    uv run ruff format .
    Set-Location '{{justfile_directory()}}\webapp'
    npx @biomejs/biome check --write .

# Linting & formatting (SOTA mandatory)
check: fmt lint

# -- Test ------------------------------------------------------------------------

# Automated verification (SOTA mandatory)
test:
    Set-Location '{{justfile_directory()}}'
    uv run --extra test pytest tests -q
    Write-Host 'Backend tests passed' -ForegroundColor Green
    Set-Location '{{justfile_directory()}}\webapp'
    npx playwright test
    Write-Host 'E2E tests passed' -ForegroundColor Green

# -- Build -----------------------------------------------------------------------

# Install all dependencies (SOTA mandatory)
bootstrap:
    uv sync --extra test --extra dev
    uv run pre-commit install
    Set-Location webapp; npm ci; if ($LASTEXITCODE -ne 0) { npm install }
    Write-Host "Pre-commit hooks installed." -ForegroundColor Green

build: bootstrap

# Build MCPB package
package:
    Set-Location '{{justfile_directory()}}'
    uv run python build_mcpb.py

# Build PyInstaller sidecar binary → native/binaries/
build-sidecar:
    Set-Location '{{justfile_directory()}}'
    powershell.exe -NoProfile -File '{{justfile_directory()}}\native\build-sidecar.ps1'

# Build Tauri desktop app — sidecar must exist first
build-native:
    Set-Location '{{justfile_directory()}}\native'
    $env:Path = "$env:USERPROFILE\.cargo\bin;$env:Path"
    npm install
    npx @tauri-apps/cli build

# Sidecar then Tauri release
build-all: build-sidecar build-native

# Build Tauri app in debug mode
build-native-debug:
    Set-Location '{{justfile_directory()}}\native'
    $env:Path = "$env:USERPROFILE\.cargo\bin;$env:Path"
    npm install
    npx @tauri-apps/cli build --debug

# -- Security -------------------------------------------------------------------

# Bandit security audit
check-sec:
    Set-Location '{{justfile_directory()}}'
    uv run bandit -r src/

# Safety dependency audit
audit-deps:
    Set-Location '{{justfile_directory()}}'
    uv run safety check

# -- Dev -------------------------------------------------------------------------

# Repo statistics
stats:
    Set-Location '{{justfile_directory()}}'
    uv run python tools/repo_stats.py

# Copy src/email_mcp → mcp-server/
copy-mcp:
    uv run python copy_server.py

# Run MCP server (stdio)
run:
    uv run python -m email_mcp.server

# Start web dashboard (backend + frontend)
serve dev:
    Set-Location '{{justfile_directory()}}'
    .\start.ps1

# -- Housekeeping ---------------------------------------------------------------

# Clean build artifacts and backups
clean:
    Set-Location '{{justfile_directory()}}'
    -Remove-Item -Recurse -Force build/, dist/, target/, .coverage, *.bak, *.spec 2>$null
    -Remove-Item -Recurse -Force src/**/*.bak, src/**/*.spec, webapp/**/*.bak 2>$null
    Get-ChildItem -Recurse -Filter __pycache__ | Remove-Item -Recurse -Force 2>$null
    Write-Host 'Cleaned' -ForegroundColor Green

# CI pipeline: build → check → test
ci: build check test
