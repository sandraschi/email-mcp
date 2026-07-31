"""Entry point for PyInstaller-bundled email-mcp backend."""

import _strptime  # noqa: F401
import sys

sys.path.insert(0, ".")

from email_mcp.server import main

main()
