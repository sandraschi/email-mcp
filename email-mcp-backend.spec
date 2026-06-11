# -*- mode: python ; coding: utf-8 -*-
# Tauri sidecar build — single-file executable (no COLLECT / one-dir)
from PyInstaller.utils.hooks import copy_metadata

datas = [("src/email_mcp", "email_mcp")]
datas += copy_metadata("fastmcp")
datas += copy_metadata("fastapi")
datas += copy_metadata("uvicorn")
datas += copy_metadata("pydantic")
datas += copy_metadata("starlette")

a = Analysis(
    ["run_server.py"],
    pathex=["src"],
    binaries=[],
    datas=datas,
    hiddenimports=[
    "_strptime",
    "_datetime",
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.asyncio",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.httptools_impl",
        "uvicorn.protocols.http.h11_impl",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.websockets_impl",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        "email_mcp.ai",
        "email_mcp.auth",
        "email_mcp.lab",
        "email_mcp.mailing_lists",
        "email_mcp.sanitize",
        "email_mcp.transport",
        "email_mcp.web",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

# One-file EXE — required for Tauri sidecar (externalBin)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="email-mcp-backend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
