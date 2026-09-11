"""
JARVIS Screen Capture Tool
Captures full monitor, foreground window, or cursor-centered ROI on demand (never continuously).
"""

import os
import tempfile
import time
from typing import Optional, Tuple
from PIL import Image, ImageGrab
import pyautogui
import win32gui
from .base import BaseTool, ToolResult


class ScreenTool(BaseTool):
    name = "ScreenTool"
    description = "Captures on-demand screenshots for vision understanding."

    def execute(self, action: str, **kwargs) -> ToolResult:
        action = action.lower().strip()

        if action == "capture_screen":
            path = self.capture_screen()
            return ToolResult(status="SUCCESS", message="Screen captured.", data={"image_path": path})

        elif action == "capture_cursor_region":
            path = self.capture_cursor_region()
            return ToolResult(status="SUCCESS", message="Cursor region captured.", data={"image_path": path})

        elif action == "capture_active_window":
            path = self.capture_active_window()
            return ToolResult(status="SUCCESS", message="Active window captured.", data={"image_path": path})

        return ToolResult(status="FAILED", message=f"Unknown screen action: {action}")

    def capture_screen(self) -> str:
        temp_path = os.path.join(tempfile.gettempdir(), f"jarvis_screen_{int(time.time()*1000)}.png")
        img = ImageGrab.grab()
        img.save(temp_path)
        return temp_path

    def capture_cursor_region(self, radius: int = 150) -> str:
        """Captures a bounding box centered on the current cursor position."""
        cx, cy = pyautogui.position()
        bbox = (max(0, cx - radius), max(0, cy - radius), cx + radius, cy + radius)
        temp_path = os.path.join(tempfile.gettempdir(), f"jarvis_cursor_{int(time.time()*1000)}.png")
        img = ImageGrab.grab(bbox=bbox)
        img.save(temp_path)
        return temp_path

    def capture_active_window(self) -> str:
        hwnd = win32gui.GetForegroundWindow()
        if hwnd:
            rect = win32gui.GetWindowRect(hwnd)
            temp_path = os.path.join(tempfile.gettempdir(), f"jarvis_window_{int(time.time()*1000)}.png")
            img = ImageGrab.grab(bbox=rect)
            img.save(temp_path)
            return temp_path
        return self.capture_screen()
