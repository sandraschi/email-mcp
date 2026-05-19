#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::sync::Mutex;
use tauri::{Emitter, Manager};
use tauri_plugin_shell::ShellExt;

struct BackendProcess(Mutex<Option<tauri_plugin_shell::process::CommandChild>>);

/// Start the MCP Python backend server. Called on app launch.
#[tauri::command]
async fn start_backend(app: tauri::AppHandle, state: tauri::State<'_, BackendProcess>) -> Result<String, String> {
    let resource_dir = app.path().resource_dir().map_err(|e| e.to_string())?;
    let project_root = resource_dir
        .parent()
        .unwrap_or(std::path::Path::new("."));

    let cmd = app.shell()
        .command("uv")
        .args(["run", "python", "-m", "email_mcp.server", "--mode", "http", "--port", "10813"])
        .current_dir(project_root);

    let (mut rx, child) = cmd.spawn().map_err(|e| format!("Failed to start backend: {}", e))?;
    *state.0.lock().unwrap() = Some(child);

    tauri::async_runtime::spawn(async move {
        use tauri_plugin_shell::process::CommandEvent;
        while let Some(event) = rx.recv().await {
            if let CommandEvent::Stdout(line) = event {
                let text = String::from_utf8_lossy(&line);
                if text.contains("Uvicorn running") || text.contains("Application startup") {
                    break;
                }
            }
        }
    });

    Ok("Backend starting on port 10813".into())
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_process::init())
        .manage(BackendProcess(Mutex::new(None)))
        .invoke_handler(tauri::generate_handler![start_backend])
        .setup(|app| {
            let handle = app.handle().clone();
            tauri::async_runtime::spawn(async move {
                let _ = handle.emit("backend-status", "starting");
                match start_backend(handle.clone(), handle.state::<BackendProcess>()).await {
                    Ok(_) => { let _ = handle.emit("backend-status", "ready"); }
                    Err(e) => { let _ = handle.emit("backend-status", format!("error: {}", e)); }
                }
            });

            #[cfg(debug_assertions)]
            if let Some(window) = app.get_webview_window("main") {
                window.open_devtools();
            }
            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(|app, event| {
            if let tauri::RunEvent::Exit = event {
                if let Some(child) = app.state::<BackendProcess>().0.lock().unwrap().take() {
                    let _ = child.kill();
                }
            }
        });
}
