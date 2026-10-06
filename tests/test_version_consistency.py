"""Every place that states the release version must agree with email_mcp.__version__.

The version used to be a string literal in ~10 source locations and 6 metadata files and had
drifted (0.4.1 / 0.5.0 / 0.5.1 side by side), so the installer, the bundle and the server all
reported different versions.
"""

import json
import re
import tomllib
from pathlib import Path

import email_mcp

ROOT = Path(__file__).resolve().parent.parent


def _json_version(rel: str) -> str:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))["version"]


def test_metadata_files_match_package_version():
    expected = email_mcp.__version__
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    mcpb_pyproject = tomllib.loads((ROOT / "mcpb" / "pyproject.toml").read_text(encoding="utf-8"))
    found = {
        "pyproject.toml": pyproject["project"]["version"],
        "mcpb/pyproject.toml": mcpb_pyproject["project"]["version"],
        "mcpb/manifest.json": _json_version("mcpb/manifest.json"),
        "native/tauri.conf.json": _json_version("native/tauri.conf.json"),
        "glama.json": _json_version("glama.json"),
        "manifest.json": _json_version("manifest.json"),
    }
    assert found == dict.fromkeys(found, expected)


def test_lockfile_entry_for_this_package_matches():
    lock = (ROOT / "uv.lock").read_text(encoding="utf-8")
    match = re.search(r'^name = "email-mcp"\nversion = "([^"]+)"', lock, re.MULTILINE)
    assert match, "email-mcp entry not found in uv.lock"
    assert match.group(1) == email_mcp.__version__


def test_no_hardcoded_release_version_literals_in_source():
    """server.py / web.py / tool_registry.py must read __version__, not repeat a literal."""
    literal = re.compile(r'["\']v?0\.[0-9]+\.[0-9]+["\']|Server v0\.[0-9]+\.[0-9]+')
    offenders = []
    for path in (ROOT / "src" / "email_mcp").rglob("*.py"):
        for no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if literal.search(line) and "__version__" not in line and ">=" not in line:
                offenders.append(f"{path.relative_to(ROOT)}:{no}: {line.strip()[:80]}")
    assert offenders == []
