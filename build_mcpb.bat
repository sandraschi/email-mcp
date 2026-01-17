@echo off
echo Building Email MCP MCPB Package...
echo.

cd /d %~dp0

if not exist "mcp-server" (
    echo Error: mcp-server directory not found
    echo Make sure to run this from the minimail-mcp directory
    pause
    exit /b 1
)

python build_mcpb.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo MCPB package built successfully!
    echo.
    echo Next steps:
    echo 1. Open Claude Desktop
    echo 2. Go to Settings - MCP Servers
    echo 3. Drag and drop minimail-mcp.mcpb into the window
    echo 4. Configure your email settings in the server config
    echo.
    echo The server will then be available in Claude Desktop!
) else (
    echo.
    echo Failed to build MCPB package.
    echo Make sure Python is installed and all required files are present.
)

echo.
pause