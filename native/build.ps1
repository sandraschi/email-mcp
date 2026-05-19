#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Build the email-mcp Tauri native app for Windows.
.DESCRIPTION
    Installs Tauri prerequisites if needed, then builds the app.
    Requires: Rust + Cargo (install via rustup.rs), Visual Studio Build Tools.
#>
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Write-Host "═══ email-mcp Tauri Build ═══" -ForegroundColor Cyan

# Step 1: Build the webapp
Write-Host "→ Building webapp..." -ForegroundColor Yellow
Push-Location "$Root\webapp"
try {
    npm install
    npm run build
}
finally {
    Pop-Location
}

# Step 2: Check Tauri CLI
$tauriBin = (Get-Command "npx" -ErrorAction SilentlyContinue)
if (-not $tauriBin) {
    Write-Error "Node.js/npx not found. Install from https://nodejs.org"
    exit 1
}

Write-Host "→ Building Tauri app..." -ForegroundColor Yellow
Push-Location "$Root\native"
try {
    npx @tauri-apps/cli build
}
finally {
    Pop-Location
}

Write-Host "═══ Build complete ═══" -ForegroundColor Green
Write-Host "Installer: $Root\native\target\release\bundle\nsis\email-mcp-native_0.1.0_x64-setup.exe" -ForegroundColor Cyan
