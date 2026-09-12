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
    }
    if let Ok(val) = std::env::var("GEMINI_API_KEY") {
        if !val.trim().is_empty() {
            return Ok(val.trim().to_string());
        }
    }
    Err("GEMINI_API_KEY not configured in .env".to_string())
}

#[command]
pub fn capture_screen() -> Result<String, String> {
    let output = std::process::Command::new("powershell")
        .args(["-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", r#"
            Add-Type -AssemblyName System.Windows.Forms
            Add-Type -AssemblyName System.Drawing
            $b = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
            $bmp = New-Object System.Drawing.Bitmap($b.Width, $b.Height)
            $g = [System.Drawing.Graphics]::FromImage($bmp)
            $g.CopyFromScreen($b.Location, [System.Drawing.Point]::Empty, $b.Size)
            $ms = New-Object System.IO.MemoryStream
            $bmp.Save($ms, [System.Drawing.Imaging.ImageFormat]::Jpeg)
            $bytes = $ms.ToArray()
            $g.Dispose()
            $bmp.Dispose()
            $ms.Dispose()
            [Convert]::ToBase64String($bytes)
        "#])
        .output()
        .map_err(|e| format!("Failed to execute powershell: {}", e))?;

    if output.status.success() {
        let b64 = String::from_utf8_lossy(&output.stdout).trim().to_string();
        if !b64.is_empty() {
            return Ok(b64);
        }
    }
    Err(String::from_utf8_lossy(&output.stderr).to_string())
}

#[command]
pub fn set_clipboard(text: String) -> Result<(), String> {
    let mut child = std::process::Command::new("powershell")
        .args(["-NoProfile", "-Command", "$input | Set-Clipboard"])
        .stdin(std::process::Stdio::piped())
        .spawn()
        .map_err(|e| e.to_string())?;

    if let Some(mut stdin) = child.stdin.take() {
        use std::io::Write;
        let _ = stdin.write_all(text.as_bytes());
    }
    let _ = child.wait();
    Ok(())
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

