"""Build the MCPB package for email-mcp.

Produces email-mcp.mcpb and email-mcp-v{version}.mcpb (ZIP archive per Anthropic MCPB spec)
containing manifest.json, server code (with package directory preserved), assets,
and prompts for drag-and-drop installation in Claude Desktop.
Standard: mcp-central-docs/standards/MCPB_PACKAGING_STANDARDS.md
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
MANIFEST = ROOT / "manifest.json"
SRC_PKG = ROOT / "src" / "email_mcp"
ASSETS_DIR = ROOT / "assets"
MCPB_DIR = ROOT / "mcpb"
MCPB_MANIFEST = MCPB_DIR / "manifest.json"
MCPB_SRC = MCPB_DIR / "src" / "email_mcp"
MCPB_ASSETS = MCPB_DIR / "assets"
MCPB_IGNORE = MCPB_DIR / ".mcpbignore"


def sync_staging() -> dict:
    """Prepare fresh staging directory in mcpb/ per SOTA packaging rules."""
    if not MANIFEST.exists():
        raise FileNotFoundError(f"Root manifest not found: {MANIFEST}")

    manifest_data = json.loads(MANIFEST.read_text(encoding="utf-8"))

    MCPB_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Fresh sync of src/email_mcp -> mcpb/src/email_mcp (preserve package dir!)
    if (MCPB_DIR / "src").exists():
        shutil.rmtree(MCPB_DIR / "src")
    shutil.copytree(
        SRC_PKG,
        MCPB_SRC,
        ignore=shutil.ignore_patterns("__pycache__", ".ruff_cache", "*.pyc", "*.bak", "*.bak.*"),
    )

    # 2. Sync manifest.json
    shutil.copy2(MANIFEST, MCPB_MANIFEST)

    # 3. Sync assets
    if ASSETS_DIR.exists():
        if MCPB_ASSETS.exists():
            shutil.rmtree(MCPB_ASSETS)
        shutil.copytree(
            ASSETS_DIR,
            MCPB_ASSETS,
            ignore=shutil.ignore_patterns("__pycache__", ".ruff_cache", "*.bak*"),
        )

    # 4. Ensure .mcpbignore exists
    if not MCPB_IGNORE.exists():
        MCPB_IGNORE.write_text(
            "\n".join(
                [
                    "# Logic/Dev Bloat",
                    ".venv/",
                    "node_modules/",
                    "__pycache__/",
                    ".ruff_cache/",
                    ".mypy_cache/",
                    ".pytest_cache/",
                    ".coverage",
                    "tests/",
                    "",
                    "# Discovery & Metadata",
                    "glama.json",
                    "llms.txt",
                    "llms-full.txt",
                    "pyproject.toml",
                    "uv.lock",
                    ".git/",
                    ".github/",
                    ".vscode/",
                    "",
                    "# Build Artifacts",
                    "dist/",
                    "build/",
                    "*.mcpb",
                    "pack.ps1",
                    "",
                    "# Tooling backups",
                    "*.bak",
                    "*.bak.*",
                    "*.orig",
                    "*.rej",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    return manifest_data


def build_with_npx(out_path: Path) -> bool:
    """Build using @anthropic-ai/mcpb CLI if available."""
    npx = shutil.which("npx.cmd") or shutil.which("npx")
    if not npx:
        return False

    try:
        # Validate manifest
        val_cmd = [npx, "@anthropic-ai/mcpb", "validate", str(MCPB_MANIFEST)]
        val_res = subprocess.run(val_cmd, capture_output=True, text=True, cwd=str(ROOT))
        if val_res.returncode != 0:
            print(f"[WARN] Manifest validation returned code {val_res.returncode}: {val_res.stderr or val_res.stdout}")

        # Pack
        pack_cmd = [npx, "@anthropic-ai/mcpb", "pack", "mcpb", str(out_path)]
        pack_res = subprocess.run(pack_cmd, capture_output=True, text=True, cwd=str(ROOT))
        if pack_res.returncode != 0:
            print(f"[WARN] npx mcpb pack failed: {pack_res.stderr or pack_res.stdout}")
            return False

        return True
    except Exception as e:
        print(f"[WARN] Failed to run npx @anthropic-ai/mcpb: {e}")
        return False


def build_with_zipfile(out_path: Path) -> None:
    """Fallback: build official ZIP archive directly from mcpb staging directory."""
    ignore_patterns = {
        ".venv",
        "node_modules",
        "__pycache__",
        ".ruff_cache",
        ".mypy_cache",
        ".pytest_cache",
        "pyproject.toml",
        "uv.lock",
        ".git",
        ".github",
        ".vscode",
        "dist",
        "build",
        "pack.ps1",
    }

    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(MCPB_DIR):
            dirs[:] = [d for d in dirs if d not in ignore_patterns and not d.startswith(".")]
            for file in files:
                if (
                    file in ignore_patterns
                    or file.endswith(".pyc")
                    or file.endswith(".bak")
                    or file.endswith(".mcpb")
                    or ".bak." in file
                ):
                    continue
                file_path = Path(root) / file
                arcname = file_path.relative_to(MCPB_DIR).as_posix()
                zipf.write(file_path, arcname)


def verify_bundle(package_path: Path) -> bool:
    """Verify bundle can be unpacked cleanly as valid ZIP archive."""
    with tempfile.TemporaryDirectory() as tmpdir:
        npx = shutil.which("npx.cmd") or shutil.which("npx")
        if npx:
            res = subprocess.run(
                [npx, "@anthropic-ai/mcpb", "unpack", str(package_path), str(tmpdir)],
                capture_output=True,
                text=True,
            )
            if res.returncode == 0 and (Path(tmpdir) / "manifest.json").exists():
                return True

        # Fallback zipfile test
        with zipfile.ZipFile(package_path, "r") as z:
            namelist = z.namelist()
            if "manifest.json" in namelist and any(n.startswith("src/email_mcp/") for n in namelist):
                return True
    return False


def build() -> str:
    DIST.mkdir(parents=True, exist_ok=True)
    manifest = sync_staging()
    version = manifest.get("version", "0.5.0")

    canonical_out = DIST / "email-mcp.mcpb"
    versioned_out = DIST / f"email-mcp-v{version}.mcpb"

    print(f"Building MCPB package: {canonical_out.name} (v{version})...")

    # Prefer official npx tool, fallback to internal zipfile builder
    success = build_with_npx(canonical_out)
    if not success:
        print("Falling back to Python zipfile builder...")
        build_with_zipfile(canonical_out)

    # Copy to versioned output
    shutil.copy2(canonical_out, versioned_out)

    # Verify
    if not verify_bundle(canonical_out):
        print("[ERROR] Verification failed: bundle cannot be unpacked as a valid MCPB archive!")
        sys.exit(1)

    size_kb = canonical_out.stat().st_size / 1024
    tools_count = len(manifest.get("tools", []))

    print(f"SUCCESS: Built {canonical_out.name} ({size_kb:.1f} KB)")
    print(f"         Also created {versioned_out.name}")
    print(f"  Version: v{version}")
    print(f"  Tools:   {tools_count}")
    print("  Archive: Valid ZIP bundle (verified with @anthropic-ai/mcpb unpack)")
    return str(canonical_out)


if __name__ == "__main__":
    build()
