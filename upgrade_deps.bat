@echo off
cd /d D:\Dev\repos\email-mcp
echo === email-mcp: upgrading to FastMCP 3.2 + prefab-ui 0.18 ===

set UV=C:\Users\sandr\.local\bin\uv.exe

echo.
echo [1/3] Installing fastmcp ^>=3.2.0 and prefab-ui ^>=0.18.0 ...
%UV% pip install "fastmcp>=3.2.0,<4" "prefab-ui>=0.18.0"
if errorlevel 1 (
    echo FAILED: uv pip install
    pause
    exit /b 1
)

echo.
echo [2/3] Installing package in editable mode ...
%UV% pip install -e .
if errorlevel 1 (
    echo FAILED: editable install
    pause
    exit /b 1
)

echo.
echo [3/3] Verifying versions ...
%UV% run python -c "import fastmcp, importlib.metadata as m; print('fastmcp', fastmcp.__version__); print('prefab-ui', m.version('prefab-ui'))"

echo.
echo === Done. Press any key to close. ===
pause
