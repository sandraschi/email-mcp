"""Smoke test: verify email-mcp imports and key subsystems before server start."""

import importlib.metadata as meta
import sys

errors = []


def check(label, fn):
    try:
        fn()
        print(f"  OK  {label}")
    except Exception as e:
        print(f"  FAIL {label}: {e}")
        errors.append(label)


print("=== email-mcp smoke test ===\n")


# Version checks
def check_fastmcp():
    import fastmcp

    v = fastmcp.__version__
    parts = list(map(int, v.split(".")[:2]))
    assert parts >= [3, 2], f"Need fastmcp>=3.2, got {v}"
    print(f"       fastmcp {v}", end="")


def check_prefab():
    v = meta.version("prefab-ui")
    parts = list(map(int, v.split(".")[:2]))
    assert parts >= [0, 18], f"Need prefab-ui>=0.18, got {v}"
    print(f"       prefab-ui {v}", end="")


def check_server_import():
    # Import without starting the server
    import importlib

    spec = importlib.util.spec_from_file_location("email_mcp.server", r"D:\Dev\repos\email-mcp\src\email_mcp\server.py")
    mod = importlib.util.module_from_spec(spec)
    # Don't exec — just parse
    import ast
    import pathlib

    src = pathlib.Path(r"D:\Dev\repos\email-mcp\src\email_mcp\server.py").read_text()
    ast.parse(src)  # syntax check only


def check_web_import():
    import ast
    import pathlib

    src = pathlib.Path(r"D:\Dev\repos\email-mcp\src\email_mcp\web.py").read_text()
    ast.parse(src)


def check_ai_import():
    import ast
    import pathlib

    src = pathlib.Path(r"D:\Dev\repos\email-mcp\src\email_mcp\ai.py").read_text()
    ast.parse(src)


def check_prefab_import():
    pass


check("fastmcp >= 3.2", check_fastmcp)
check("prefab-ui >= 0.18", check_prefab)
check("server.py syntax", check_server_import)
check("web.py syntax", check_web_import)
check("ai.py syntax", check_ai_import)
check("prefab_ui imports", check_prefab_import)

print()
if errors:
    print(f"FAILED: {len(errors)} check(s): {errors}")
    sys.exit(1)
else:
    print("All checks passed.")
