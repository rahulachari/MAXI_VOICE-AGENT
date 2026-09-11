use std::sync::atomic::{AtomicBool, Ordering};
use tauri::{AppHandle, Emitter, Manager};
use windows::Win32::UI::Input::KeyboardAndMouse::{
    GetAsyncKeyState, VK_CONTROL, VK_MENU
};

static RUNNING: AtomicBool = AtomicBool::new(false);

pub fn start_hook(app: AppHandle) {
    if RUNNING.swap(true, Ordering::SeqCst) {
        return;
    }

    std::thread::spawn(move || {
        let mut was_active = false;

        while RUNNING.load(Ordering::SeqCst) {
            std::thread::sleep(std::time::Duration::from_millis(25));

            // Query physical hardware state of Ctrl and Alt keys
            let ctrl_down = unsafe { (GetAsyncKeyState(VK_CONTROL.0 as i32) as u16 & 0x8000) != 0 };
            let alt_down = unsafe { (GetAsyncKeyState(VK_MENU.0 as i32) as u16 & 0x8000) != 0 };
            let is_active = ctrl_down && alt_down;

            if is_active && !was_active {
                was_active = true;
                if let Some(win) = app.get_webview_window("main") {
                    let _ = win.show();
                    let _ = win.set_focus();
                }
                let _ = app.emit("shortcut-triggered", serde_json::json!({ "action": "down" }));
            } else if !is_active && was_active {
                was_active = false;
                let _ = app.emit("shortcut-triggered", serde_json::json!({ "action": "up" }));
            }
        }
    });
}

pub fn stop_hook() {
    RUNNING.store(false, Ordering::SeqCst);
}
