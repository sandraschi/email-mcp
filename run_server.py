"""Entry point for PyInstaller-bundled email-mcp backend -- dual transport.

- MCP_PORT set (Tauri spawn): run HTTP/uvicorn on 127.0.0.1:{MCP_PORT}.
- Otherwise: run stdio (Claude Desktop / Cursor).
"""

import _strptime  # noqa: F401
import faulthandler
import os
import sys

# Crash tripwire: dump the Python traceback to stderr on segfault/abort so a
# silent native death (onnxruntime, IMAP C-ext) leaves evidence in the NSSM logs.
faulthandler.enable()

sys.path.insert(0, ".")


def _prune_rotated_logs(keep_days: int = 14, keep_min: int = 10) -> None:
    """Delete rotated service-*.log files older than keep_days.

    NSSM rotates the live log on every service start and never cleans up
    (yesterday: 928 files / 208 MB). Keep the newest keep_min files
    regardless of age so a quiet box never loses its last evidence.
    Never breaks startup: all errors are swallowed.
    """
    try:
        import time

        repo_root = os.path.dirname(os.path.abspath(__file__))
        log_dir = os.path.join(repo_root, "logs")
        if not os.path.isdir(log_dir):
            return
        cutoff = time.time() - keep_days * 86400
        rotated = []
        for name in os.listdir(log_dir):
            if name.startswith("service-") and name.endswith(".log") and os.path.isfile(os.path.join(log_dir, name)):
                # Live NSSM targets have no timestamp infix; only prune rotated ones.
                if "-20" in name:
                    rotated.append(name)
        rotated.sort()
        # Only old files beyond the newest keep_min are eligible.
        doomed = [
            n for n in rotated[: max(0, len(rotated) - keep_min)] if os.path.getmtime(os.path.join(log_dir, n)) < cutoff
        ]
        for name in doomed:
            try:
                os.remove(os.path.join(log_dir, name))
            except OSError:
                pass
    except Exception:
        pass


_prune_rotated_logs()

from email_mcp.server import main

# Service mode only (LocalSystem has SeDebugPrivilege): clean up session 0 zombies holding the
# dev frontend port 10812. Skipped when the Tauri shell spawned us (EMAIL_MCP_TAURI=1) - a
# desktop app must never kill whatever listens on a port, that is the developer's own Vite
# dev server (TAURI_PRODUCTION_PITFALLS section 15).
if not os.environ.get("EMAIL_MCP_TAURI"):
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
