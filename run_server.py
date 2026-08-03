"""Entry point for PyInstaller-bundled email-mcp backend -- dual transport.

- MCP_PORT set (Tauri spawn): run HTTP/uvicorn on 127.0.0.1:{MCP_PORT}.
- Otherwise: run stdio (Claude Desktop / Cursor).
"""

import _strptime  # noqa: F401
import os
import sys

sys.path.insert(0, ".")

from email_mcp.server import main

port = os.environ.get("MCP_PORT") or os.environ.get("PORT")
if port:
    host = os.environ.get("MCP_HOST", "127.0.0.1")
    # Overwrite sys.argv BEFORE main(): PyInstaller leaves the frozen args in
    # place and server.main() parses them with argparse.
    sys.argv = ["run_server.py", "--http", "--host", host, "--port", str(port)]

main()
