"""
JARVIS Multi-Monitor Detection Helper
Determines which physical monitor contains the user's active foreground window.
"""

from typing import Tuple
from PySide6.QtCore import QRect
from PySide6.QtGui import QGuiApplication
import win32gui
import win32process
import win32api
import win32con


def get_active_window_info() -> dict:
    """Returns foreground window handle, title, process name, and bounding rect."""
    hwnd = win32gui.GetForegroundWindow()
    if not hwnd:
        return {"hwnd": 0, "title": "", "process": "", "rect": (0, 0, 0, 0)}

    title = win32gui.GetWindowText(hwnd)
    rect = win32gui.GetWindowRect(hwnd)  # (left, top, right, bottom)

    process_name = ""
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        handle = win32api.OpenProcess(win32con.PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if handle:
            process_name = win32process.GetModuleFileNameEx(handle, 0)
            process_name = process_name.split("\\")[-1]
            win32api.CloseHandle(handle)
    except Exception:
        pass

    return {
        "hwnd": hwnd,
        "title": title,
        "process": process_name,
        "rect": rect,
    }


def get_active_monitor_geometry() -> QRect:
    """
    Returns the QRect geometry of the monitor containing the active foreground window.
    Falls back to primary screen if detection fails.
    """
    app = QGuiApplication.instance()
    if not app:
        return QRect(0, 0, 1920, 1080)

    screens = app.screens()
    if not screens:
        return QRect(0, 0, 1920, 1080)

    try:
        hwnd = win32gui.GetForegroundWindow()
        if hwnd:
            hmon = win32api.MonitorFromWindow(hwnd, win32con.MONITOR_DEFAULTTONEAREST)
            mon_info = win32api.GetMonitorInfo(hmon)
            rc_work = mon_info["Work"]  # (left, top, right, bottom)
            return QRect(rc_work[0], rc_work[1], rc_work[2] - rc_work[0], rc_work[3] - rc_work[1])
    except Exception as e:
        print(f"[MonitorHelper] Failed to query active monitor: {e}")

    # Fallback to primary screen
    primary = app.primaryScreen()
    return primary.availableGeometry() if primary else QRect(0, 0, 1920, 1080)
