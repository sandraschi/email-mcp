"""Build the MCPB package for email-mcp.

Produces minimail-mcp.mcpb — a gzipped tarball containing manifest.json,
server code, and assets for drag-and-drop installation in Claude Desktop.
"""

import json
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
MANIFEST = ROOT / "manifest.json"
SERVER_DIR = ROOT / "src" / "email_mcp"
ASSETS_DIR = ROOT / "assets"

INCLUDE_EXTS = {".py", ".md", ".txt", ".json", ".toml", ".png", ".svg", ".ico"}
EXCLUDE_DIRS = {"__pycache__", ".git", ".venv", "node_modules"}


def build() -> str:
    DIST.mkdir(parents=True, exist_ok=True)
    out_path = DIST / "email-mcp.mcpb"

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    with tarfile.open(out_path, "w:gz") as tar:
        tar.add(MANIFEST, arcname="manifest.json")

        for f in SERVER_DIR.rglob("*"):
            if f.is_dir() and f.name in EXCLUDE_DIRS:
                continue
            if f.is_file() and f.suffix in INCLUDE_EXTS:
                arc = f.relative_to(ROOT).as_posix()
                tar.add(f, arcname=arc)

        readme = ROOT / "README.md"
        if readme.exists():
            tar.add(readme, arcname="README.md")

        if ASSETS_DIR.exists():
            for f in ASSETS_DIR.rglob("*"):
                if f.is_file() and f.suffix in INCLUDE_EXTS:
                    arc = f.relative_to(ROOT).as_posix()
                    tar.add(f, arcname=arc)

    size = out_path.stat().st_size
    print(f"Built {out_path.name} ({size / 1024:.0f} KB)")
    print(f"  Server: email-mcp v{manifest.get('version', '?.?.?')}")
    print(f"  Tools:  {len(manifest.get('tools', []))}")
    return str(out_path)


if __name__ == "__main__":
    build()
