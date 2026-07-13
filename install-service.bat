@echo off
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Please run as Administrator
    pause
    exit /b 1
)

set NSSM="C:\Program Files\Jellyfin\Server\nssm.exe"
set DIR=%~dp0

%NSSM% stop email-mcp 2>nul
%NSSM% remove email-mcp confirm 2>nul

%NSSM% install email-mcp "%DIR%run-email-service.bat"
%NSSM% set email-mcp AppDirectory "%DIR%"
%NSSM% set email-mcp AppStdout "%DIR%logs\service-stdout.log"
%NSSM% set email-mcp AppStderr "%DIR%logs\service-stderr.log"
%NSSM% set email-mcp Start SERVICE_AUTO_START
%NSSM% set email-mcp AppRotateFiles 1
%NSSM% set email-mcp AppRotateSeconds 86400
%NSSM% set email-mcp AppRotateBytes 10485760

%NSSM% start email-mcp
echo email-mcp service installed and started
