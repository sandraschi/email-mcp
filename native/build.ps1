#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Full release build: PyInstaller sidecar + Tauri Windows installer.
.DESCRIPTION
    1. Builds webapp (Vite)
    2. Builds PyInstaller sidecar binary → native/binaries/
    3. Builds Tauri app → native/target/release/bundle/nsis/
    Requires: Rust + Cargo (rustup.rs), Node.js 20+, uv, VS Build Tools.
#>
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Write-Host "══ email-mcp Tauri Release Build ══" -ForegroundColor Cyan

# Step 1: Build the webapp
Write-Host "→ [1/3] Building webapp..." -ForegroundColor Yellow
Push-Location "$Root\webapp"
try {
    npm install
    npm run build
} finally { Pop-Location }

# Step 2: Build PyInstaller sidecar
Write-Host "→ [2/3] Building PyInstaller sidecar..." -ForegroundColor Yellow
pwsh -NoLogo -File "$Root\native\build-sidecar.ps1"

# Step 3: Build Tauri app
Write-Host "→ [3/3] Building Tauri app..." -ForegroundColor Yellow
Push-Location "$Root\native"
try {
    $env:Path = "$env:USERPROFILE\.cargo\bin;$env:Path"
    npm install
    npx @tauri-apps/cli build
} finally { Pop-Location }

$installer = "$Root\native\target\release\bundle\nsis\email-mcp-native_0.1.0_x64-setup.exe"
Write-Host "══ Build complete ══" -ForegroundColor Green
Write-Host "Installer: $installer" -ForegroundColor Cyan
