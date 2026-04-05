#!/usr/bin/env python3
"""Sync canonical package under src/email_mcp into mcp-server/src/email_mcp for MCPB / mirrors."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC_PKG = ROOT / "src" / "email_mcp"
DST_PKG = ROOT / "mcp-server" / "src" / "email_mcp"

FILES = ("server.py", "mailing_lists.py")


def main() -> None:
    DST_PKG.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        src = SRC_PKG / name
        dst = DST_PKG / name
        if not src.is_file():
            raise SystemExit(f"Missing {src}")
        shutil.copy2(src, dst)
        print(f"Copied {src.relative_to(ROOT)} -> {dst.relative_to(ROOT)}")

    skills_src = SRC_PKG / "skills"
    skills_dst = DST_PKG / "skills"
    if skills_src.is_dir():
        if skills_dst.exists():
            shutil.rmtree(skills_dst)
        shutil.copytree(skills_src, skills_dst)
        print(f"Copied {skills_src.relative_to(ROOT)} -> {skills_dst.relative_to(ROOT)}")
    else:
        print("No skills/ to copy (optional).")


if __name__ == "__main__":
    main()
