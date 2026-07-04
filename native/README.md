# email-mcp Tauri Native Wrapper

Desktop app wrapper for the email-mcp webapp using **Tauri 2.0**.

## Prerequisites

- **Rust** (install via [rustup.rs](https://rustup.rs/))
- **Node.js 20+**
- **Visual Studio Build Tools** (Windows) or `pkg-config` + `libwebkit2gtk-4.1-dev` (Linux)
- Python 3.12+ with `uv` for the backend

## Development

```powershell
# Start the backend first
cd .. && .\start.ps1

# Then run the Tauri dev server
cd native
npx @tauri-apps/cli dev
```

## Build

```powershell
.\native\build.ps1
```

The installer will be at `native/target/release/bundle/nsis/`.

## Architecture

```
Tauri (Rust) ←──→ Webapp (Vite, :10812) ←─proxied─→ Backend (FastAPI, :10813)
```

- Tauri hosts the webapp in a native WebView window
- The webapp communicates with the MCP backend via HTTP (proxy configured in `vite.config.ts`)
- No Python is bundled -- the backend runs as a separate process
- Rust tray icon allows system tray minimisation
