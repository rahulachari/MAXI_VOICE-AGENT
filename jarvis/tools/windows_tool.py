"""
JARVIS Windows Tool
Manages Windows application lifecycle, window state (minimize/maximize/focus), power, and system controls.
"""

import os
import subprocess
import time
import ctypes
from typing import Optional, List, Dict
import win32gui
import win32con
import win32process
import win32api
from .base import BaseTool, ToolResult

APP_ALIASES: Dict[str, List[str]] = {
    "notepad": ["notepad.exe", "notepad"],
    "calculator": ["calc.exe", "calc"],
    "settings": ["ms-settings:", "settings"],
    "task manager": ["taskmgr.exe", "taskmgr"],
    "explorer": ["explorer.exe", "file explorer", "files"],
    "vscode": ["code", "visual studio code", "vs code"],
    "chrome": ["chrome.exe", "google chrome"],
    "edge": ["msedge.exe", "microsoft edge"],
    "terminal": ["wt.exe", "cmd.exe", "powershell.exe"],
    "paint": ["mspaint.exe"],
    "word": ["winword.exe", "microsoft word"],
    "excel": ["excel.exe", "microsoft excel"],
    "powerpoint": ["powerpnt.exe", "microsoft powerpoint"],
    "outlook": ["outlook.exe", "microsoft outlook"],
    "teams": ["ms-teams:", "microsoft teams"],
    "whatsapp": ["start whatsapp:", "whatsapp"],
    "telegram": ["start telegram:", "telegram"],
    "discord": ["discord.exe", "start discord:"],
    "spotify": ["start spotify:", "spotify"],
    "vlc": ["vlc.exe"],
    "obs": ["obs64.exe", "obs studio"],
    "snipping tool": ["snippingtool.exe", "snip & sketch"],
    "photos": ["ms-photos:", "photos"],
    "camera": ["microsoft.windows.camera:", "camera"],
    "clock": ["ms-clock:", "clock"],
    "maps": ["bingmaps:", "maps"],
    "store": ["ms-windows-store:", "microsoft store"],
    "mail": ["outlookmail:", "mail"],
    "calendar": ["outlookcal:", "calendar"],
    "cmd": ["cmd.exe"],
    "powershell": ["powershell.exe"],
    "firefox": ["firefox.exe"],
    "brave": ["brave.exe"],
    "zoom": ["zoom.exe"],
    "skype": ["start skype:", "skype"],
    "steam": ["steam.exe"],
    "epic games": ["epicgameslauncher.exe"],
    "git bash": ["git-bash.exe"],
    "figma": ["figma.exe"],
    "notion": ["notion.exe"],
}


class WindowsTool(BaseTool):
    name = "WindowsTool"
    description = "Controls Windows applications, window states, and system functions."

    def execute(self, action: str, **kwargs) -> ToolResult:
        action = action.lower().strip()

        if action == "launch_app":
            app_name = kwargs.get("app_name", "").strip()
            return self.launch_app(app_name)

        elif action == "close_app":
            app_name = kwargs.get("app_name", "").strip()
            return self.close_app(app_name)

        elif action == "focus_app":
            app_name = kwargs.get("app_name", "").strip()
            return self.focus_app(app_name)

        elif action in ["minimize_window", "minimize"]:
            return self.minimize_active_window()

        elif action in ["maximize_window", "maximize"]:
            return self.maximize_active_window()

        elif action in ["lock_pc", "lock"]:
            return self.lock_workstation()

        elif action in ["close_active", "close_window", "close_this"]:
            return self.close_active_window()

        elif action in ["volume_up", "volume_down", "mute"]:
            return self.control_volume(action)

        elif action == "set_volume":
            level = kwargs.get("level", 50)
            return self.set_volume_level(level)

        elif action == "shutdown":
            if kwargs.get("confirmed"):
                os.system("shutdown /s /t 5")
                return ToolResult(status="SUCCESS", message="Shutting down in 5 seconds.")
            return ToolResult(
                status="REQUIRES_CONFIRMATION",
                message="Are you sure you want to shut down?",
                requires_confirmation=True,
                confirmation_prompt="Shut down the computer?",
            )

        elif action == "restart_pc":
            if kwargs.get("confirmed"):
                os.system("shutdown /r /t 5")
                return ToolResult(status="SUCCESS", message="Restarting in 5 seconds.")
            return ToolResult(
                status="REQUIRES_CONFIRMATION",
                message="Are you sure you want to restart?",
                requires_confirmation=True,
                confirmation_prompt="Restart the computer?",
            )

        elif action == "sleep_pc":
            try:
                os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
                return ToolResult(status="SUCCESS", message="Putting computer to sleep.")
            except Exception as e:
                return ToolResult(status="FAILED", message=f"Failed to sleep: {e}")

        elif action == "brightness_up":
            return self._adjust_brightness(+10)

        elif action == "brightness_down":
            return self._adjust_brightness(-10)

        return ToolResult(status="FAILED", message=f"Unknown Windows action: {action}")

    def launch_app(self, app_name: str) -> ToolResult:
        if not app_name:
            return ToolResult(status="FAILED", message="No application specified to launch.")

        target_cmd = None
        clean_name = app_name.lower().strip()

        # Check alias dictionary
        for key, aliases in APP_ALIASES.items():
            if clean_name == key or clean_name in key or any(clean_name == a or clean_name in a for a in aliases):
                target_cmd = aliases[0]
                break

        if not target_cmd:
            target_cmd = app_name

        try:
            if target_cmd.startswith("ms-") or target_cmd.startswith("start ") or ":" in target_cmd:
                cmd = target_cmd if target_cmd.startswith("start ") else f"start {target_cmd}"
                subprocess.Popen(cmd, shell=True)
            else:
                # Try launching via start command so Windows shell resolves path or registered app
                subprocess.Popen(f'start "" "{target_cmd}"', shell=True)

            display_name = app_name.strip().title()
            return ToolResult(
                status="SUCCESS",
                message=f"Opening {display_name} for you.",
                data={"app": app_name, "full_details": f"🚀 Launching application: {display_name}"},
            )
        except Exception as e:
            # Fallback to direct subprocess
            try:
                subprocess.Popen(target_cmd, shell=True)
                display_name = app_name.strip().title()
                return ToolResult(
                    status="SUCCESS",
                    message=f"Opening {display_name}.",
                    data={"app": app_name, "full_details": f"🚀 Launching application: {display_name}"},
                )
            except Exception as e2:
                return ToolResult(
                    status="FAILED",
                    message=f"I couldn't launch {app_name}. Please verify that it is installed.",
                    error=str(e2),
                )

    def close_app(self, app_name: str) -> ToolResult:
        hwnd = self._find_window_by_title_or_process(app_name)
        if hwnd:
            try:
                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                return ToolResult(status="SUCCESS", message=f"Closed {app_name.capitalize()}.")
            except Exception as e:
                return ToolResult(status="FAILED", message=f"Failed to close {app_name}: {e}")

        # Fallback to taskkill
        try:
            exe_name = app_name.lower()
            if not exe_name.endswith(".exe"):
                exe_name += ".exe"
            subprocess.run(f"taskkill /IM {exe_name} /F", shell=True, capture_output=True)
            return ToolResult(status="SUCCESS", message=f"Closed {app_name.capitalize()}.")
        except Exception as e:
            return ToolResult(status="FAILED", message=f"Could not close {app_name}: {e}")

    def focus_app(self, app_name: str) -> ToolResult:
        hwnd = self._find_window_by_title_or_process(app_name)
        if hwnd:
            try:
                # Restore if minimized
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(hwnd)
                return ToolResult(status="SUCCESS", message=f"Switched to {app_name.capitalize()}.")
            except Exception as e:
                return ToolResult(status="FAILED", message=f"Failed to switch to {app_name}: {e}")

        return ToolResult(status="FAILED", message=f"Could not find an open window for {app_name}.")

    def close_active_window(self) -> ToolResult:
        hwnd = win32gui.GetForegroundWindow()
        if hwnd:
            try:
                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                return ToolResult(status="SUCCESS", message="Window closed.")
            except Exception as e:
                return ToolResult(status="FAILED", message=f"Failed to close window: {e}")
        return ToolResult(status="FAILED", message="No active window to close.")

    def minimize_active_window(self) -> ToolResult:
        hwnd = win32gui.GetForegroundWindow()
        if hwnd:
            win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
            return ToolResult(status="SUCCESS", message="Window minimized.")
        return ToolResult(status="FAILED", message="No active window to minimize.")

    def maximize_active_window(self) -> ToolResult:
        hwnd = win32gui.GetForegroundWindow()
        if hwnd:
            win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
            return ToolResult(status="SUCCESS", message="Window maximized.")
        return ToolResult(status="FAILED", message="No active window to maximize.")

    def lock_workstation(self) -> ToolResult:
        try:
            ctypes.windll.user32.LockWorkStation()
            return ToolResult(status="SUCCESS", message="PC locked.")
        except Exception as e:
            return ToolResult(status="FAILED", message=f"Failed to lock workstation: {e}")

    def control_volume(self, action: str) -> ToolResult:
        VK_VOLUME_MUTE = 0xAD
        VK_VOLUME_DOWN = 0xAE
        VK_VOLUME_UP = 0xAF

        if action == "volume_up":
            for _ in range(5):
                win32api.keybd_event(VK_VOLUME_UP, 0, 0, 0)
                win32api.keybd_event(VK_VOLUME_UP, 0, win32con.KEYEVENTF_KEYUP, 0)
            return ToolResult(status="SUCCESS", message="Volume turned up.")
        elif action == "volume_down":
            for _ in range(5):
                win32api.keybd_event(VK_VOLUME_DOWN, 0, 0, 0)
                win32api.keybd_event(VK_VOLUME_DOWN, 0, win32con.KEYEVENTF_KEYUP, 0)
            return ToolResult(status="SUCCESS", message="Volume turned down.")
        elif action == "mute":
            win32api.keybd_event(VK_VOLUME_MUTE, 0, 0, 0)
            win32api.keybd_event(VK_VOLUME_MUTE, 0, win32con.KEYEVENTF_KEYUP, 0)
            return ToolResult(status="SUCCESS", message="Volume muted.")
        return ToolResult(status="FAILED", message="Invalid volume command.")

    def set_volume_level(self, level: int) -> ToolResult:
        """Set volume to a specific percentage using repeated key presses."""
        try:
            VK_VOLUME_DOWN = 0xAE
            VK_VOLUME_UP = 0xAF
            # First mute then unmute to reset, then press up proportionally
            # Each press = ~2% volume. Set to 0 first with 50 downs, then up.
            for _ in range(50):
                win32api.keybd_event(VK_VOLUME_DOWN, 0, 0, 0)
                win32api.keybd_event(VK_VOLUME_DOWN, 0, win32con.KEYEVENTF_KEYUP, 0)
            steps = max(0, min(50, level // 2))
            for _ in range(steps):
                win32api.keybd_event(VK_VOLUME_UP, 0, 0, 0)
                win32api.keybd_event(VK_VOLUME_UP, 0, win32con.KEYEVENTF_KEYUP, 0)
            return ToolResult(status="SUCCESS", message=f"Volume set to {level}%.")
        except Exception as e:
            return ToolResult(status="FAILED", message=f"Failed to set volume: {e}")

    def _adjust_brightness(self, delta: int) -> ToolResult:
        """Adjust screen brightness using WMI (Windows Management Instrumentation)."""
        try:
            import wmi
            c = wmi.WMI(namespace='wmi')
            methods = c.WmiMonitorBrightnessMethods()[0]
            current = c.WmiMonitorBrightness()[0].CurrentBrightness
            new_level = max(0, min(100, current + delta))
            methods.WmiSetBrightness(new_level, 0)
            return ToolResult(status="SUCCESS", message=f"Brightness set to {new_level}%.")
        except Exception:
            # Fallback: use PowerShell
            try:
                direction = "up" if delta > 0 else "down"
                subprocess.run(
                    f'powershell -Command "(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, [Math]::Max(0, [Math]::Min(100, (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness).CurrentBrightness + {delta})))"',
                    shell=True,
                    capture_output=True,
                )
                return ToolResult(status="SUCCESS", message=f"Brightness adjusted {direction}.")
            except Exception as e2:
                return ToolResult(status="FAILED", message=f"Could not adjust brightness: {e2}")

    def _verify_app_running(self, app_name: str) -> bool:
        return self._find_window_by_title_or_process(app_name) is not None

    def _find_window_by_title_or_process(self, query: str) -> Optional[int]:
        query = query.lower()
        matched_hwnd = None

        def enum_cb(hwnd, _):
            nonlocal matched_hwnd
            if not win32gui.IsWindowVisible(hwnd):
                return True
            title = win32gui.GetWindowText(hwnd).lower()
            if query in title:
                matched_hwnd = hwnd
                return False
            return True

        win32gui.EnumWindows(enum_cb, None)
        return matched_hwnd
