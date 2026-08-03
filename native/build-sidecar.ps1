#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Build the PyInstaller sidecar binary for the Tauri native wrapper.
.DESCRIPTION
    Produces a single-file email-mcp-backend.exe and copies it to
    native/binaries/ with the Tauri target-triple suffix.
    Requires: uv, Python 3.12+, pyinstaller (installed via uv if absent).
#>
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Write-Host "=== email-mcp sidecar build ===" -ForegroundColor Cyan

Push-Location $Root
try {
    # Ensure PyInstaller is available in the PROJECT venv (uv tool env lacks
    # fastmcp metadata and fails with PackageNotFoundError)
    $pyiExe = "$Root\.venv\Scripts\pyinstaller.exe"
    if (-not (Test-Path $pyiExe)) {
        Write-Host "-> Installing PyInstaller in project venv..." -ForegroundColor Yellow
        uv add --dev pyinstaller
    }

    # Clean previous build artefacts
    Remove-Item -Recurse -Force "$Root\build\email-mcp-backend" -ErrorAction SilentlyContinue
    Remove-Item -Force "$Root\dist\email-mcp-backend.exe" -ErrorAction SilentlyContinue

    Write-Host "-> Running PyInstaller..." -ForegroundColor Yellow
    & $pyiExe email-mcp-backend.spec --clean --noconfirm
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed (exit $LASTEXITCODE)" }

    # Tauri expects the binary named with the target triple
    $triple = "x86_64-pc-windows-msvc"
    $src = "$Root\dist\email-mcp-backend.exe"
    $dstDir = "$Root\native\binaries"
    $dst = "$dstDir\email-mcp-backend-$triple.exe"

    if (-not (Test-Path $src)) { throw "Build output not found: $src" }

    New-Item -ItemType Directory -Path $dstDir -Force | Out-Null
    Copy-Item $src $dst -Force

    $sizeMB = [math]::Round((Get-Item $dst).Length / 1MB, 1)
    Write-Host "=== Sidecar ready ===" -ForegroundColor Green
    Write-Host "  $dst ($sizeMB MB)" -ForegroundColor Cyan
} finally {
    Pop-Location
}
