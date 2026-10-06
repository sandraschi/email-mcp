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
        "email_mcp.autorespond",
        "email_mcp.connectors",
        "email_mcp.contacts",
        "email_mcp.curated_lists",
        "email_mcp.lab",
        "email_mcp.mailing_lists",
        "email_mcp.oauth",
        "email_mcp.sanitize",
        "email_mcp.scheduler",
        "email_mcp.services.email_services",
        "email_mcp.services.graph_service",
        "email_mcp.signatures",
        "email_mcp.templates",
        "email_mcp.tools.tool_registry",
        "email_mcp.transport",
        "email_mcp.watcher",
        "email_mcp.web",
        "email_mcp.workflows",
        "psutil",
        "_strptime",
    ],
    hookspath=[],

    hooksconfig={},
    runtime_hooks=[],
    # The RAG stack is NOT frozen into the desktop sidecar (RAG_ADDON_STANDARD.md): it is hundreds
    # of MB and cannot live in a onefile exe. email_mcp.server registers the RAG tools lazily and
    # degrades when these are missing, so excluding them is safe - and it keeps the build
    # independent of whatever happens to be installed in the venv (a re-synced venv once added
    # ~150 MB, 197 MB backend / 200 MB installer instead of 47 / 49).
    excludes=[
        "lancedb",
        "lance",
        "pyarrow",
        "fastembed",
        "onnxruntime",
        "tokenizers",
        "huggingface_hub",
        "hf_xet",
    ],
    noarchive=True,
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
