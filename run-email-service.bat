@echo off
cd /d "%~dp0"
setlocal enabledelayedexpansion

:: Load .env if present
if exist "%~dp0.env" (
    for /f "usebackq delims=" %%a in ("%~dp0.env") do (
        set %%a
    )
)

"%~dp0.venv\Scripts\python.exe" -m email_mcp.server --http --port 10813
