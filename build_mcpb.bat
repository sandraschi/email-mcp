@echo off
cd /d %~dp0
uv run python build_mcpb.py
if %ERRORLEVEL% EQU 0 (
    echo.
    echo Build successful!
    echo Drag and drop dist\email-mcp.mcpb into Claude Desktop MCP Servers settings.
) else (
    echo.
    echo Build failed.
)
echo.
pause
