"""Entry point for PyInstaller-bundled email-mcp backend -- dual transport.

- MCP_PORT set (Tauri spawn): run HTTP/uvicorn on 127.0.0.1:{MCP_PORT}.
- Otherwise: run stdio (Claude Desktop / Cursor).
"""

import _strptime  # noqa: F401
import os
import sys

sys.path.insert(0, ".")

from email_mcp.server import main

# LocalSystem has SeDebugPrivilege; clean up any session 0 zombies holding frontend port 10812
try:
    import re
    import subprocess

    res = subprocess.run(["netstat", "-ano", "-p", "tcp"], capture_output=True, text=True)
    for line in res.stdout.splitlines():
        if ":10812" in line and "LISTENING" in line:
            m = re.search(r"(\d+)\s*$", line.strip())
            if m:
                target_pid = m.group(1)
                subprocess.run(["taskkill", "/F", "/T", "/PID", target_pid], capture_output=True)
except Exception:
    pass

port = os.environ.get("MCP_PORT") or os.environ.get("PORT") or os.environ.get("WEB_PORT")
if not port and "--stdio" not in sys.argv:
    port = "10813"

if port and "--stdio" not in sys.argv:
    host = os.environ.get("MCP_HOST", "127.0.0.1")
    # Overwrite sys.argv BEFORE main(): PyInstaller leaves the frozen args in
    # place and server.main() parses them with argparse.
    sys.argv = ["run_server.py", "--http", "--host", host, "--port", str(port)]

main()
