use tauri::command;
use windows::core::{PCWSTR, w};
use windows::Win32::UI::Shell::ShellExecuteW;
use windows::Win32::UI::WindowsAndMessaging::SW_SHOWNORMAL;
use std::ffi::OsStr;
use std::os::windows::ffi::OsStrExt;

fn win_shell_open(target: &str) {
    let mut wide: Vec<u16> = OsStr::new(target).encode_wide().collect();
    wide.push(0);
    unsafe {
        let _ = ShellExecuteW(
            None,
            w!("open"),
            PCWSTR(wide.as_ptr()),
            None,
            None,
            SW_SHOWNORMAL,
        );
    }
}

#[command]
pub fn execute_action(action: String, target: String) -> Result<String, String> {
    match action.as_str() {
        "open_url" => {
            let url = if !target.starts_with("http://") && !target.starts_with("https://") {
                format!("https://{}", target)
            } else {
                target.clone()
            };
            win_shell_open(&url);
            Ok(format!("Opened {}", url))
        }
        "search_web" => {
            let search_url = format!("https://www.google.com/search?q={}", urlencoding::encode(&target));
            win_shell_open(&search_url);
            Ok(format!("Searched for {}", target))
        }
        "launch_app" => {
            win_shell_open(&target);
            Ok(format!("Launched {}", target))
        }
        _ => {
            // General or URL fallback
            if target.starts_with("http") {
                win_shell_open(&target);
            }
            Ok(format!("Executed action {}", action))
        }
    }
}

#[command]
pub fn hide_notch(window: tauri::WebviewWindow) -> Result<(), String> {
    window.hide().map_err(|e| e.to_string())
}

#[command]
pub fn show_notch(window: tauri::WebviewWindow) -> Result<(), String> {
    window.show().map_err(|e| e.to_string())?;
    let _ = window.set_focus();
    Ok(())
}

#[command]
pub fn get_gemini_key() -> Result<String, String> {
    // Check .env in parent directories or return user configured key
    if let Ok(content) = std::fs::read_to_string(".env") {
        for line in content.lines() {
            if let Some(val) = line.strip_prefix("GEMINI_API_KEY=") {
                let trimmed = val.trim();
                if !trimmed.is_empty() {
                    return Ok(trimmed.to_string());
                }
            }
        }
    }
    if let Ok(content) = std::fs::read_to_string("../.env") {
        for line in content.lines() {
            if let Some(val) = line.strip_prefix("GEMINI_API_KEY=") {
                let trimmed = val.trim();
                if !trimmed.is_empty() {
                    return Ok(trimmed.to_string());
                }
            }
        }
    if let Ok(val) = std::env::var("GEMINI_API_KEY") {
        if !val.trim().is_empty() {
            return Ok(val.trim().to_string());
        }
    }
    Err("GEMINI_API_KEY not configured in .env".to_string())
}

#[command]
pub fn open_linkedin_profile(name: String, company: String, query_hint: String) -> Result<String, String> {
    let query = format!("site:linkedin.com/in/ \"{}\" \"{}\" {}", name, company, query_hint);
    let search_url = format!("https://www.google.com/search?q={}", urlencoding::encode(&query));
    win_shell_open(&search_url);
    Ok(format!("Opening {}'s LinkedIn profile.", name))
}

#[command]
pub fn explain_visual_content(_summary: String, _deep_dive: String, _key_takeaways: Vec<String>) -> Result<(), String> {
    Ok(())
}

#[command]
pub fn general_web_action(search_query: String, target_platform: String) -> Result<String, String> {
    let search_url = format!("https://www.google.com/search?q={}+{}", urlencoding::encode(&search_query), urlencoding::encode(&target_platform));
    win_shell_open(&search_url);
    Ok(format!("Executing general web action for {}", search_query))
}
