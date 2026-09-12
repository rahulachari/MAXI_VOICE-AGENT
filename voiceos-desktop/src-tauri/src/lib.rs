use tauri::Manager;

pub mod hook;
pub mod actions;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    std::panic::set_hook(Box::new(|info| {
        let _ = std::fs::write("panic.log", format!("PANIC: {:#?}", info));
    }));
    let _ = std::fs::write("app.log", "VoiceOS started\n");

    tauri::Builder::default()
        .setup(|app| {
            let window = app.get_webview_window("main").unwrap();
            
            // Disable native OS window shadow to prevent dark bounding box
            let _ = window.set_shadow(false);

            // Center the floating notch at the top of the primary display
            if let Ok(Some(monitor)) = window.primary_monitor() {
                let monitor_pos = monitor.position();
                let screen_width = monitor.size().width as i32;
                let scale_factor = monitor.scale_factor();
                let win_width = (540.0 * scale_factor) as i32;
                let x = monitor_pos.x + (screen_width - win_width) / 2;
                let y = monitor_pos.y + (12.0 * scale_factor) as i32;
                let _ = window.set_position(tauri::Position::Physical(tauri::PhysicalPosition { x, y }));
            }

            println!("VoiceOS is running in background! Press and hold [Ctrl] + [Alt] to talk.");
            hook::start_hook(app.handle().clone());
            Ok(())
        })
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![
            actions::execute_action,
            actions::hide_notch,
            actions::show_notch,
            actions::get_gemini_key,
            actions::capture_screen,
            actions::set_clipboard,
            actions::open_linkedin_profile,
            actions::explain_visual_content,
            actions::general_web_action
        ])
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(|_app_handle, _event| {});
}
