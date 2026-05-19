#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::Manager;
use tauri_plugin_shell::ShellExt;

/// Launch the MCP backend server as a sidecar.
#[tauri::command]
async fn start_backend(app: tauri::AppHandle) -> Result<String, String> {
    let sidecar = app
        .shell()
        .sidecar("start-backend")
        .map_err(|e| e.to_string())?
        .args(["--mode", "http", "--port", "10813"]);

    let (mut _rx, _child) = sidecar
        .spawn()
        .map_err(|e| format!("Failed to start backend: {}", e))?;

    // Give backend a moment to start
    std::thread::sleep(std::time::Duration::from_secs(2));
    Ok("Backend started on port 10813".into())
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_process::init())
        .invoke_handler(tauri::generate_handler![start_backend])
        .setup(|app| {
            #[cfg(debug_assertions)]
            {
                let window = app.get_webview_window("main").unwrap();
                window.open_devtools();
            }
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
