"""
JARVIS Chrome Browser Adapter
Manages Google Chrome process launching, window focusing, and tab control.
"""

import os
import subprocess
import webbrowser
from typing import Optional
import win32gui
import win32con


class ChromeAdapter:
    @classmethod
    def is_chrome_open(cls) -> bool:
        return cls.get_chrome_hwnd() is not None

    @classmethod
    def get_chrome_hwnd(cls) -> Optional[int]:
        chrome_hwnd = None

        def enum_cb(hwnd, _):
            nonlocal chrome_hwnd
            if not win32gui.IsWindowVisible(hwnd):
                return True
            cls_name = win32gui.GetClassName(hwnd)
            title = win32gui.GetWindowText(hwnd).lower()
            if cls_name == "Chrome_WidgetWin_1" or "chrome" in title:
                chrome_hwnd = hwnd
                return False
            return True

        win32gui.EnumWindows(enum_cb, None)
        return chrome_hwnd

    @classmethod
    def focus_chrome(cls) -> bool:
        hwnd = cls.get_chrome_hwnd()
        if hwnd:
            try:
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(hwnd)
                return True
            except Exception:
                pass
        return False

    @classmethod
    def open_url(cls, url: str) -> bool:
        # Launch using default browser or explicit Chrome
        try:
            webbrowser.open(url)
            return True
        except Exception as e:
            print(f"[ChromeAdapter] Failed to open URL: {e}")
            try:
                os.system(f'start "" "{url}"')
                return True
            except Exception:
                return False
