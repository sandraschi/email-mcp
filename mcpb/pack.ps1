#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Pack email-mcp into SOTA .mcpb bundle for Claude Desktop.
    Standard: mcp-central-docs/standards/MCPB_PACKAGING_STANDARDS.md
#>
$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path $PSScriptRoot -Parent
Set-Location $RepoRoot

Write-Host "Building email-mcp MCPB package..." -ForegroundColor Cyan
uv run python build_mcpb.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "MCPB build failed with exit code $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}
