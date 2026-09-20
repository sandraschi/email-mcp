# Fleet unified launcher - do not edit logic here.
# Change fleet-start.config.ps1 at the repo root instead.
param(
    [switch]$Headless,
    [switch]$BackendOnly,
    [switch]$FrontendOnly,
    [switch]$NoBrowser,
    [switch]$ReuseIfRunning
)

$ErrorActionPreference = 'Stop'
# Bi-modal launcher (NAKED_PC_INSTALL_STANDARD section 8): fleet engine when
# mcp-central-docs is beside the fleet root, standalone naked-PC fallback
# otherwise. A public clone has no D: drive and no mcp-central-docs sibling.
$ReposRoot = if ($env:FLEET_REPOS_ROOT) { $env:FLEET_REPOS_ROOT } else { 'D:\Dev\repos' }
# NOTE: Join-Path throws when the drive does not exist (naked PC has no D:),
# so only build the engine path when the fleet root is actually there.
$EnginePath = $null
if (Test-Path -LiteralPath $ReposRoot) {
    $EnginePath = Join-Path $ReposRoot 'mcp-central-docs\scripts\Invoke-FleetWebappStart.ps1'
}

$configCandidates = @(
    (Join-Path $PSScriptRoot 'fleet-start.config.ps1'),
    (Join-Path (Split-Path -Parent $PSScriptRoot) 'fleet-start.config.ps1')
)
$configPath = $null
foreach ($candidate in $configCandidates) {
    if (Test-Path -LiteralPath $candidate) {
        $configPath = $candidate
        break
    }
}
if (-not $configPath) {
    Write-Host 'ERROR: Missing fleet-start.config.ps1 (repo root or beside start.ps1).' -ForegroundColor Red
    exit 1
}

# Mode 1: Central Fleet Engine (when mcp-central-docs is available)
if ($EnginePath -and (Test-Path -LiteralPath $EnginePath)) {
    . $EnginePath
    Start-FleetWebapp @PSBoundParameters -ConfigPath $configPath -LauncherRoot $PSScriptRoot
    exit 0
}

# Mode 2: Standalone (naked PC / public clone without mcp-central-docs).
# Brings its own prereqs via winget and launches from this repo's own
# fleet-start.config.ps1 - nothing outside the clone is assumed.
Write-Host 'Central fleet engine not found - starting in standalone mode.' -ForegroundColor Yellow

function Require-Command {
    param([string]$Cmd, [string]$WingetId, [string]$Label)
    if (Get-Command $Cmd -ErrorAction SilentlyContinue) { return }
    Write-Host "  $Label not found - installing via winget ..." -ForegroundColor Yellow
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        Write-Host "ERROR: winget unavailable. Install $Label manually ($WingetId)." -ForegroundColor Red
        exit 1
    }
    winget install --id $WingetId --source winget --silent --accept-source-agreements --accept-package-agreements --disable-interactivity
    $env:PATH = [System.Environment]::GetEnvironmentVariable('PATH', 'Machine') + ';' + `
                [System.Environment]::GetEnvironmentVariable('PATH', 'User')
    if (-not (Get-Command $Cmd -ErrorAction SilentlyContinue)) {
        Write-Host "Installed $Label but '$Cmd' still not in PATH. Reopen PowerShell and retry." -ForegroundColor Yellow
        exit 1
    }
}
Require-Command 'uv' 'astral-sh.uv' 'uv (Python package manager)'
Require-Command 'node' 'OpenJS.NodeJS.LTS' 'Node.js LTS'
Require-Command 'npm' 'OpenJS.NodeJS.LTS' 'npm'
Require-Command 'just' 'Casey.Just' 'just (command runner)'

$cfg = . $configPath
$repoRoot = Split-Path -Parent $PSScriptRoot
if (Test-Path (Join-Path $PSScriptRoot 'pyproject.toml')) { $repoRoot = $PSScriptRoot }

$uvExe = (Get-Command uv).Source
$npmExe = (Get-Command npm).Source

$backendPort = if ($cfg.BackendPort) { [int]$cfg.BackendPort } else { 10813 }
$frontendPort = if ($cfg.FrontendPort) { [int]$cfg.FrontendPort } else { 10812 }
$healthPath = if ($cfg.HealthPath) { $cfg.HealthPath } else { '/health' }

$webRel = if ($cfg.WebRoot) { $cfg.WebRoot } else { 'webapp' }
$webRoot = if ([System.IO.Path]::IsPathRooted($webRel)) { $webRel } else { Join-Path $repoRoot $webRel }
if (-not (Test-Path -LiteralPath $webRoot)) { $webRoot = $PSScriptRoot }

# 0. Sync Python environment (uv fetches its own CPython - no system Python needed)
$syncArgs = @('sync', '--project', $repoRoot)
foreach ($extra in @($cfg.Backend.SyncExtras) | Where-Object { $_ }) { $syncArgs += @('--extra', $extra) }
Write-Host 'Syncing Python environment (uv sync) ...' -ForegroundColor Cyan
& $uvExe @syncArgs
if ($LASTEXITCODE -ne 0) {
    Write-Host 'ERROR: uv sync failed - see output above.' -ForegroundColor Red
    exit 1
}

# 0b. Install frontend dependencies only when node_modules is absent
if (-not (Test-Path (Join-Path $webRoot 'node_modules'))) {
    Write-Host 'Installing frontend dependencies (npm install) ...' -ForegroundColor Cyan
    Push-Location $webRoot
    & $npmExe install --prefer-offline
    $npmExit = $LASTEXITCODE
    Pop-Location
    if ($npmExit -ne 0) {
        Write-Host 'ERROR: npm install failed - see output above.' -ForegroundColor Red
        exit 1
    }
}

# 0c. Explicit vite guard (vite is a local devDependency, never global)
$viteLocal = Join-Path $webRoot 'node_modules\.bin\vite'
if ((-not $BackendOnly) -and $frontendPort -gt 0 -and -not (Test-Path -LiteralPath $viteLocal)) {
    Write-Host 'ERROR: vite missing from node_modules after npm install.' -ForegroundColor Red
    Write-Host "Delete '$webRoot\node_modules' and re-run." -ForegroundColor Yellow
    exit 1
}

$target = if ($cfg.Backend.UvicornTarget) { $cfg.Backend.UvicornTarget } else { 'app.main:app' }
$module = ($target -split ':')[0]

# 0d. Import smoke-test before the health-wait loop (fail in 2s, not 90s)
& $uvExe run --project $repoRoot python -c "import $module; print('  [ok] Import OK')"
if ($LASTEXITCODE -ne 0) {
    Write-Host 'ERROR: import check failed - see output above.' -ForegroundColor Red
    exit 1
}

$backendExec = if ($cfg.Backend.Kind -eq 'module-serve') {
    $mod = if ($cfg.Backend.Module) { $cfg.Backend.Module } else { $cfg.Name }
    $args = if ($cfg.Backend.ServeArgs) { $cfg.Backend.ServeArgs } else { '--serve' }
    "python -m $mod $args"
} elseif ($cfg.Backend.Kind -eq 'cli-serve') {
    $mod = if ($cfg.Backend.Module) { $cfg.Backend.Module } else { $cfg.Name }
    "$mod --serve --port $backendPort"
} else {
    "uvicorn $target --host 127.0.0.1 --port $backendPort"
}

# 1. Start Backend
$startedBackend = ((-not $FrontendOnly) -and $backendPort -gt 0 -and $cfg.Backend.Kind -ne 'none')
if ($startedBackend) {
    Write-Host "Starting backend on :$backendPort ..." -ForegroundColor Cyan
    $bWorkDir = if ($cfg.Backend.WorkDir) {
        if ([System.IO.Path]::IsPathRooted($cfg.Backend.WorkDir)) { $cfg.Backend.WorkDir } else { Join-Path $repoRoot $cfg.Backend.WorkDir }
    } else { $repoRoot }

    $pyPath = if ($cfg.Backend.PythonPath) {
        $parts = $cfg.Backend.PythonPath -split ';' | ForEach-Object {
            if ([System.IO.Path]::IsPathRooted($_)) { $_ } else { Join-Path $repoRoot $_ }
        }
        $parts -join ';'
    } else { "$repoRoot;$repoRoot\src" }

    $bCmd = "`$env:PYTHONPATH = '$pyPath'; `$env:WEB_PORT = '$backendPort'; Set-Location '$bWorkDir'; uv run --project '$repoRoot' $backendExec"
    Start-Process powershell.exe -ArgumentList @('-NoProfile', '-NoExit', '-Command', $bCmd) -WorkingDirectory $bWorkDir
}

# 2. Start Frontend
if (-not $BackendOnly -and $frontendPort -gt 0 -and (Test-Path -LiteralPath $webRoot)) {
    Write-Host "Starting frontend on :$frontendPort ..." -ForegroundColor Cyan
    if ($cfg.Frontend.PortEnvVar) { Set-Item -Path "Env:$($cfg.Frontend.PortEnvVar)" -Value "$frontendPort" }
    if ($cfg.Frontend.ApiTargetEnv) { Set-Item -Path "Env:$($cfg.Frontend.ApiTargetEnv)" -Value "http://127.0.0.1:$backendPort" }

    $cmdFlag = if ($Headless) { '/c' } else { '/k' }
    if ($cfg.Frontend.Kind -eq 'next') {
        Start-Process cmd.exe -ArgumentList @($cmdFlag, "npm run dev -- -p $frontendPort -H 127.0.0.1") -WorkingDirectory $webRoot
    } else {
        Start-Process cmd.exe -ArgumentList @($cmdFlag, "npm run dev -- --port $frontendPort --host 127.0.0.1") -WorkingDirectory $webRoot
    }
}

# 3. Wait for backend health (fail loud with the direct-run command)
if ($startedBackend) {
    $healthUrl = "http://127.0.0.1:$backendPort$healthPath"
    Write-Host "Waiting for backend health at $healthUrl ..." -ForegroundColor Cyan
    $deadline = (Get-Date).AddSeconds(90)
    $ready = $false
    while ((Get-Date) -lt $deadline) {
        try {
            $r = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
            if ([int]$r.StatusCode -eq 200) { $ready = $true; break }
        } catch { }
        Start-Sleep -Seconds 3
    }
    if (-not $ready) {
        Write-Host 'ERROR: backend health timed out after 90s.' -ForegroundColor Red
        Write-Host 'Run this directly to see the error:' -ForegroundColor Yellow
        Write-Host "  cd $repoRoot; uv run --project '$repoRoot' $backendExec" -ForegroundColor Yellow
        exit 1
    }
    Write-Host '  [ok] Backend healthy.' -ForegroundColor Green
}

# 4. Open Browser
if (-not $NoBrowser -and -not $Headless -and -not $BackendOnly -and $frontendPort -gt 0) {
    Start-Process "http://127.0.0.1:$frontendPort/"
}
