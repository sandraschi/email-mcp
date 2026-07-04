@echo off
cd /d "%~dp0"
set PATH=C:\Users\sandr\.local\bin;%PATH%
"C:\Users\sandr\.local\bin\uv.exe" run python -m email_mcp.server --http --port 10813 > backend_run.log 2>&1
