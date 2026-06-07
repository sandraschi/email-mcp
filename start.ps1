Param([switch]$Headless, [switch]$BackendOnly, [switch]$FrontendOnly, [switch]$NoBrowser)

# Fast port helpers (scripts/PortHelpers.ps1)
Param([switch]$Headless, [switch]$BackendOnly, [switch]$FrontendOnly, [switch]$NoBrowser)

# --- SOTA Headless Standard 2026 ---
if ($Headless -and ($Host.Name -ne 'ConsoleHost' -or -not (Get-Variable -Name "NoRelaunch" -ErrorAction SilentlyContinue))) {
    $argList = @("-File", $PSCommandPath, "-NoRelaunch")
    if ($BackendOnly) { $argList += "-BackendOnly" }
    if ($FrontendOnly) { $argList += "-FrontendOnly" }
    $argList += "-NoBrowser"
    Start-Process pwsh.exe -ArgumentList $argList -WindowStyle Hidden
    exit
}
# -----------------------------------

$ErrorActionPreference = "Stop"
$Repo = $PSScriptRoot
$UV = "C:\Users\sandr\.local\bin\uv.exe"
$BackendPort = 10813
$FrontendPort = 10812

Write-Host "=== email-mcp 0.4.1 (FastMCP 3.2 + Prefab UI) ===" -ForegroundColor Cyan

# â”€â”€ Kill stale processes on both ports â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
foreach ($port in @($BackendPort, $FrontendPort)) {
    try {
        $procIds = Get-PortListenerPidsFast -Port $port
        foreach ($procId in $procIds) {
            try { Stop-Process -Id $procId -Force -ErrorAction Stop } catch { Write-Host "  Port $port: could not kill PID $($procId)" -ForegroundColor DarkGray }
        }
    } catch {
        # Fallback: try netstat if Get-NetTCPConnection fails
        $output = netstat -ano | Select-String ":$port\s"
        foreach ($line in $output) {
            $pid = ($line -split '\s+')[-1]
            if ($pid -and $pid -ne '0') { try { Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue } catch {} }
        }
    }
}
Start-Sleep -Milliseconds 500

# â”€â”€ Backend â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
if (-not $FrontendOnly) {
    Write-Host "[backend] Starting uvicorn on :$BackendPort ..." -ForegroundColor Yellow
    $backendProc = Start-Process -FilePath $UV `
        -ArgumentList "run","uvicorn","email_mcp.server:app",
                      "--host","127.0.0.1",
                      "--port",$BackendPort,
                      "--log-level","warning" `
        -WorkingDirectory $Repo `
        -PassThru -NoNewWindow
    Write-Host "[backend] PID $($backendProc.Id)"

    # Wait for backend to be ready (up to 15s)
    $ready = $false
    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Milliseconds 500
        try {
            $r = Invoke-WebRequest -Uri "http://127.0.0.1:$BackendPort/api/status" `
                -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
            if ($r.StatusCode -eq 200 -or $r.StatusCode -eq 401) { $ready = $true; break }
        } catch {}
    }
    if ($ready) {
        Write-Host "[backend] Ready at http://127.0.0.1:$BackendPort" -ForegroundColor Green
    } else {
        Write-Host "[backend] Did not respond in 15s - check logs" -ForegroundColor Red
    }
}

if ($BackendOnly) {
    Write-Host "Backend-only mode. Press Ctrl+C to stop."
    Wait-Process -Id $backendProc.Id
    exit
}

# â”€â”€ Frontend â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
Write-Host "[frontend] Starting Vite on :$FrontendPort ..." -ForegroundColor Yellow
$frontendProc = Start-Process -FilePath "node" `
    -ArgumentList (Join-Path $Repo "webapp\node_modules\.bin\vite") `
    -WorkingDirectory (Join-Path $Repo "webapp") `
    -PassThru -NoNewWindow
Write-Host "[frontend] PID $($frontendProc.Id)"

# Wait for frontend
$fready = $false
for ($i = 0; $i -lt 20; $i++) {
    Start-Sleep -Milliseconds 500
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:$FrontendPort" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        if ($r.StatusCode -eq 200) { $fready = $true; break }
    } catch {}
}

$url = "http://localhost:$FrontendPort"
if ($fready) {
    Write-Host "[frontend] Ready at $url" -ForegroundColor Green
    if (-not $NoBrowser) { Start-Process $url }
} else {
    Write-Host "[frontend] Not yet ready - opening anyway: $url" -ForegroundColor Yellow
    if (-not $NoBrowser) { Start-Process $url }
}

Write-Host ""
Write-Host "  Dashboard : $url" -ForegroundColor Cyan
Write-Host "  Inbox     : $url/inbox" -ForegroundColor Cyan
Write-Host "  Compose   : $url/compose" -ForegroundColor Cyan
Write-Host "  API Docs  : http://127.0.0.1:$BackendPort/docs" -ForegroundColor Cyan
Write-Host "  MCP HTTP  : http://127.0.0.1:$BackendPort/mcp" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop both processes." -ForegroundColor DarkGray

# Keep alive
try {
    while ($true) {
        Start-Sleep -Seconds 5
        if ($backendProc.HasExited)  { Write-Host "[backend] exited ($($backendProc.ExitCode))" -ForegroundColor Red }
        if ($frontendProc.HasExited) { Write-Host "[frontend] exited ($($frontendProc.ExitCode))" -ForegroundColor Red }
    }
} finally {
    Write-Host "Stopping..." -ForegroundColor Yellow
    try { Stop-Process -Id $backendProc.Id  -Force -ErrorAction SilentlyContinue } catch {}
    try { Stop-Process -Id $frontendProc.Id -Force -ErrorAction SilentlyContinue } catch {}
}
_PortHelpers = Join-Path $PSScriptRoot 'scripts\PortHelpers.ps1'
if (Test-Path -LiteralPath Param([switch]$Headless, [switch]$BackendOnly, [switch]$FrontendOnly, [switch]$NoBrowser)

# --- SOTA Headless Standard 2026 ---
if ($Headless -and ($Host.Name -ne 'ConsoleHost' -or -not (Get-Variable -Name "NoRelaunch" -ErrorAction SilentlyContinue))) {
    $argList = @("-File", $PSCommandPath, "-NoRelaunch")
    if ($BackendOnly) { $argList += "-BackendOnly" }
    if ($FrontendOnly) { $argList += "-FrontendOnly" }
    $argList += "-NoBrowser"
    Start-Process pwsh.exe -ArgumentList $argList -WindowStyle Hidden
    exit
}
# -----------------------------------

$ErrorActionPreference = "Stop"
$Repo = $PSScriptRoot
$UV = "C:\Users\sandr\.local\bin\uv.exe"
$BackendPort = 10813
$FrontendPort = 10812

Write-Host "=== email-mcp 0.4.1 (FastMCP 3.2 + Prefab UI) ===" -ForegroundColor Cyan

# â”€â”€ Kill stale processes on both ports â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
foreach ($port in @($BackendPort, $FrontendPort)) {
    try {
        $procIds = Get-PortListenerPidsFast -Port $port
        foreach ($procId in $procIds) {
            try { Stop-Process -Id $procId -Force -ErrorAction Stop } catch { Write-Host "  Port $port: could not kill PID $($procId)" -ForegroundColor DarkGray }
        }
    } catch {
        # Fallback: try netstat if Get-NetTCPConnection fails
        $output = netstat -ano | Select-String ":$port\s"
        foreach ($line in $output) {
            $pid = ($line -split '\s+')[-1]
            if ($pid -and $pid -ne '0') { try { Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue } catch {} }
        }
    }
}
Start-Sleep -Milliseconds 500

# â”€â”€ Backend â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
if (-not $FrontendOnly) {
    Write-Host "[backend] Starting uvicorn on :$BackendPort ..." -ForegroundColor Yellow
    $backendProc = Start-Process -FilePath $UV `
        -ArgumentList "run","uvicorn","email_mcp.server:app",
                      "--host","127.0.0.1",
                      "--port",$BackendPort,
                      "--log-level","warning" `
        -WorkingDirectory $Repo `
        -PassThru -NoNewWindow
    Write-Host "[backend] PID $($backendProc.Id)"

    # Wait for backend to be ready (up to 15s)
    $ready = $false
    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Milliseconds 500
        try {
            $r = Invoke-WebRequest -Uri "http://127.0.0.1:$BackendPort/api/status" `
                -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
            if ($r.StatusCode -eq 200 -or $r.StatusCode -eq 401) { $ready = $true; break }
        } catch {}
    }
    if ($ready) {
        Write-Host "[backend] Ready at http://127.0.0.1:$BackendPort" -ForegroundColor Green
    } else {
        Write-Host "[backend] Did not respond in 15s - check logs" -ForegroundColor Red
    }
}

if ($BackendOnly) {
    Write-Host "Backend-only mode. Press Ctrl+C to stop."
    Wait-Process -Id $backendProc.Id
    exit
}

# â”€â”€ Frontend â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
Write-Host "[frontend] Starting Vite on :$FrontendPort ..." -ForegroundColor Yellow
$frontendProc = Start-Process -FilePath "node" `
    -ArgumentList (Join-Path $Repo "webapp\node_modules\.bin\vite") `
    -WorkingDirectory (Join-Path $Repo "webapp") `
    -PassThru -NoNewWindow
Write-Host "[frontend] PID $($frontendProc.Id)"

# Wait for frontend
$fready = $false
for ($i = 0; $i -lt 20; $i++) {
    Start-Sleep -Milliseconds 500
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:$FrontendPort" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        if ($r.StatusCode -eq 200) { $fready = $true; break }
    } catch {}
}

$url = "http://localhost:$FrontendPort"
if ($fready) {
    Write-Host "[frontend] Ready at $url" -ForegroundColor Green
    if (-not $NoBrowser) { Start-Process $url }
} else {
    Write-Host "[frontend] Not yet ready - opening anyway: $url" -ForegroundColor Yellow
    if (-not $NoBrowser) { Start-Process $url }
}

Write-Host ""
Write-Host "  Dashboard : $url" -ForegroundColor Cyan
Write-Host "  Inbox     : $url/inbox" -ForegroundColor Cyan
Write-Host "  Compose   : $url/compose" -ForegroundColor Cyan
Write-Host "  API Docs  : http://127.0.0.1:$BackendPort/docs" -ForegroundColor Cyan
Write-Host "  MCP HTTP  : http://127.0.0.1:$BackendPort/mcp" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop both processes." -ForegroundColor DarkGray

# Keep alive
try {
    while ($true) {
        Start-Sleep -Seconds 5
        if ($backendProc.HasExited)  { Write-Host "[backend] exited ($($backendProc.ExitCode))" -ForegroundColor Red }
        if ($frontendProc.HasExited) { Write-Host "[frontend] exited ($($frontendProc.ExitCode))" -ForegroundColor Red }
    }
} finally {
    Write-Host "Stopping..." -ForegroundColor Yellow
    try { Stop-Process -Id $backendProc.Id  -Force -ErrorAction SilentlyContinue } catch {}
    try { Stop-Process -Id $frontendProc.Id -Force -ErrorAction SilentlyContinue } catch {}
}
_PortHelpers) { . Param([switch]$Headless, [switch]$BackendOnly, [switch]$FrontendOnly, [switch]$NoBrowser)

# --- SOTA Headless Standard 2026 ---
if ($Headless -and ($Host.Name -ne 'ConsoleHost' -or -not (Get-Variable -Name "NoRelaunch" -ErrorAction SilentlyContinue))) {
    $argList = @("-File", $PSCommandPath, "-NoRelaunch")
    if ($BackendOnly) { $argList += "-BackendOnly" }
    if ($FrontendOnly) { $argList += "-FrontendOnly" }
    $argList += "-NoBrowser"
    Start-Process pwsh.exe -ArgumentList $argList -WindowStyle Hidden
    exit
}
# -----------------------------------

$ErrorActionPreference = "Stop"
$Repo = $PSScriptRoot
$UV = "C:\Users\sandr\.local\bin\uv.exe"
$BackendPort = 10813
$FrontendPort = 10812

Write-Host "=== email-mcp 0.4.1 (FastMCP 3.2 + Prefab UI) ===" -ForegroundColor Cyan

# â”€â”€ Kill stale processes on both ports â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
foreach ($port in @($BackendPort, $FrontendPort)) {
    try {
        $procIds = Get-PortListenerPidsFast -Port $port
        foreach ($procId in $procIds) {
            try { Stop-Process -Id $procId -Force -ErrorAction Stop } catch { Write-Host "  Port $port: could not kill PID $($procId)" -ForegroundColor DarkGray }
        }
    } catch {
        # Fallback: try netstat if Get-NetTCPConnection fails
        $output = netstat -ano | Select-String ":$port\s"
        foreach ($line in $output) {
            $pid = ($line -split '\s+')[-1]
            if ($pid -and $pid -ne '0') { try { Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue } catch {} }
        }
    }
}
Start-Sleep -Milliseconds 500

# â”€â”€ Backend â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
if (-not $FrontendOnly) {
    Write-Host "[backend] Starting uvicorn on :$BackendPort ..." -ForegroundColor Yellow
    $backendProc = Start-Process -FilePath $UV `
        -ArgumentList "run","uvicorn","email_mcp.server:app",
                      "--host","127.0.0.1",
                      "--port",$BackendPort,
                      "--log-level","warning" `
        -WorkingDirectory $Repo `
        -PassThru -NoNewWindow
    Write-Host "[backend] PID $($backendProc.Id)"

    # Wait for backend to be ready (up to 15s)
    $ready = $false
    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Milliseconds 500
        try {
            $r = Invoke-WebRequest -Uri "http://127.0.0.1:$BackendPort/api/status" `
                -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
            if ($r.StatusCode -eq 200 -or $r.StatusCode -eq 401) { $ready = $true; break }
        } catch {}
    }
    if ($ready) {
        Write-Host "[backend] Ready at http://127.0.0.1:$BackendPort" -ForegroundColor Green
    } else {
        Write-Host "[backend] Did not respond in 15s - check logs" -ForegroundColor Red
    }
}

if ($BackendOnly) {
    Write-Host "Backend-only mode. Press Ctrl+C to stop."
    Wait-Process -Id $backendProc.Id
    exit
}

# â”€â”€ Frontend â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
Write-Host "[frontend] Starting Vite on :$FrontendPort ..." -ForegroundColor Yellow
$frontendProc = Start-Process -FilePath "node" `
    -ArgumentList (Join-Path $Repo "webapp\node_modules\.bin\vite") `
    -WorkingDirectory (Join-Path $Repo "webapp") `
    -PassThru -NoNewWindow
Write-Host "[frontend] PID $($frontendProc.Id)"

# Wait for frontend
$fready = $false
for ($i = 0; $i -lt 20; $i++) {
    Start-Sleep -Milliseconds 500
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:$FrontendPort" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        if ($r.StatusCode -eq 200) { $fready = $true; break }
    } catch {}
}

$url = "http://localhost:$FrontendPort"
if ($fready) {
    Write-Host "[frontend] Ready at $url" -ForegroundColor Green
    if (-not $NoBrowser) { Start-Process $url }
} else {
    Write-Host "[frontend] Not yet ready - opening anyway: $url" -ForegroundColor Yellow
    if (-not $NoBrowser) { Start-Process $url }
}

Write-Host ""
Write-Host "  Dashboard : $url" -ForegroundColor Cyan
Write-Host "  Inbox     : $url/inbox" -ForegroundColor Cyan
Write-Host "  Compose   : $url/compose" -ForegroundColor Cyan
Write-Host "  API Docs  : http://127.0.0.1:$BackendPort/docs" -ForegroundColor Cyan
Write-Host "  MCP HTTP  : http://127.0.0.1:$BackendPort/mcp" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop both processes." -ForegroundColor DarkGray

# Keep alive
try {
    while ($true) {
        Start-Sleep -Seconds 5
        if ($backendProc.HasExited)  { Write-Host "[backend] exited ($($backendProc.ExitCode))" -ForegroundColor Red }
        if ($frontendProc.HasExited) { Write-Host "[frontend] exited ($($frontendProc.ExitCode))" -ForegroundColor Red }
    }
} finally {
    Write-Host "Stopping..." -ForegroundColor Yellow
    try { Stop-Process -Id $backendProc.Id  -Force -ErrorAction SilentlyContinue } catch {}
    try { Stop-Process -Id $frontendProc.Id -Force -ErrorAction SilentlyContinue } catch {}
}
_PortHelpers }

# --- SOTA Headless Standard 2026 ---
if ($Headless -and ($Host.Name -ne 'ConsoleHost' -or -not (Get-Variable -Name "NoRelaunch" -ErrorAction SilentlyContinue))) {
    $argList = @("-File", $PSCommandPath, "-NoRelaunch")
    if ($BackendOnly) { $argList += "-BackendOnly" }
    if ($FrontendOnly) { $argList += "-FrontendOnly" }
    $argList += "-NoBrowser"
    Start-Process pwsh.exe -ArgumentList $argList -WindowStyle Hidden
    exit
}
# -----------------------------------

$ErrorActionPreference = "Stop"
$Repo = $PSScriptRoot
$UV = "C:\Users\sandr\.local\bin\uv.exe"
$BackendPort = 10813
$FrontendPort = 10812

Write-Host "=== email-mcp 0.4.1 (FastMCP 3.2 + Prefab UI) ===" -ForegroundColor Cyan

# â”€â”€ Kill stale processes on both ports â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
foreach ($port in @($BackendPort, $FrontendPort)) {
    try {
        $procIds = Get-PortListenerPidsFast -Port $port
        foreach ($procId in $procIds) {
            try { Stop-Process -Id $procId -Force -ErrorAction Stop } catch { Write-Host "  Port $port: could not kill PID $($procId)" -ForegroundColor DarkGray }
        }
    } catch {
        # Fallback: try netstat if Get-NetTCPConnection fails
        $output = netstat -ano | Select-String ":$port\s"
        foreach ($line in $output) {
            $pid = ($line -split '\s+')[-1]
            if ($pid -and $pid -ne '0') { try { Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue } catch {} }
        }
    }
}
Start-Sleep -Milliseconds 500

# â”€â”€ Backend â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
if (-not $FrontendOnly) {
    Write-Host "[backend] Starting uvicorn on :$BackendPort ..." -ForegroundColor Yellow
    $backendProc = Start-Process -FilePath $UV `
        -ArgumentList "run","uvicorn","email_mcp.server:app",
                      "--host","127.0.0.1",
                      "--port",$BackendPort,
                      "--log-level","warning" `
        -WorkingDirectory $Repo `
        -PassThru -NoNewWindow
    Write-Host "[backend] PID $($backendProc.Id)"

    # Wait for backend to be ready (up to 15s)
    $ready = $false
    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Milliseconds 500
        try {
            $r = Invoke-WebRequest -Uri "http://127.0.0.1:$BackendPort/api/status" `
                -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
            if ($r.StatusCode -eq 200 -or $r.StatusCode -eq 401) { $ready = $true; break }
        } catch {}
    }
    if ($ready) {
        Write-Host "[backend] Ready at http://127.0.0.1:$BackendPort" -ForegroundColor Green
    } else {
        Write-Host "[backend] Did not respond in 15s - check logs" -ForegroundColor Red
    }
}

if ($BackendOnly) {
    Write-Host "Backend-only mode. Press Ctrl+C to stop."
    Wait-Process -Id $backendProc.Id
    exit
}

# â”€â”€ Frontend â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
Write-Host "[frontend] Starting Vite on :$FrontendPort ..." -ForegroundColor Yellow
$frontendProc = Start-Process -FilePath "node" `
    -ArgumentList (Join-Path $Repo "webapp\node_modules\.bin\vite") `
    -WorkingDirectory (Join-Path $Repo "webapp") `
    -PassThru -NoNewWindow
Write-Host "[frontend] PID $($frontendProc.Id)"

# Wait for frontend
$fready = $false
for ($i = 0; $i -lt 20; $i++) {
    Start-Sleep -Milliseconds 500
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:$FrontendPort" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        if ($r.StatusCode -eq 200) { $fready = $true; break }
    } catch {}
}

$url = "http://localhost:$FrontendPort"
if ($fready) {
    Write-Host "[frontend] Ready at $url" -ForegroundColor Green
    if (-not $NoBrowser) { Start-Process $url }
} else {
    Write-Host "[frontend] Not yet ready - opening anyway: $url" -ForegroundColor Yellow
    if (-not $NoBrowser) { Start-Process $url }
}

Write-Host ""
Write-Host "  Dashboard : $url" -ForegroundColor Cyan
Write-Host "  Inbox     : $url/inbox" -ForegroundColor Cyan
Write-Host "  Compose   : $url/compose" -ForegroundColor Cyan
Write-Host "  API Docs  : http://127.0.0.1:$BackendPort/docs" -ForegroundColor Cyan
Write-Host "  MCP HTTP  : http://127.0.0.1:$BackendPort/mcp" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop both processes." -ForegroundColor DarkGray

# Keep alive
try {
    while ($true) {
        Start-Sleep -Seconds 5
        if ($backendProc.HasExited)  { Write-Host "[backend] exited ($($backendProc.ExitCode))" -ForegroundColor Red }
        if ($frontendProc.HasExited) { Write-Host "[frontend] exited ($($frontendProc.ExitCode))" -ForegroundColor Red }
    }
} finally {
    Write-Host "Stopping..." -ForegroundColor Yellow
    try { Stop-Process -Id $backendProc.Id  -Force -ErrorAction SilentlyContinue } catch {}
    try { Stop-Process -Id $frontendProc.Id -Force -ErrorAction SilentlyContinue } catch {}
}

