"""
JARVIS Keyboard Automation Tool
Semantic shortcuts, key combinations, and text entry.
"""

import time
import pyautogui
from .base import BaseTool, ToolResult

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05


class KeyboardTool(BaseTool):
    name = "KeyboardTool"
    description = "Simulates keyboard hotkeys and text input."

    def execute(self, action: str, **kwargs) -> ToolResult:
        action = action.lower().strip()

        if action == "hotkey":
            keys = kwargs.get("keys", [])
            if isinstance(keys, str):
                keys = [k.strip() for k in keys.split("+")]
            return self.hotkey(*keys)

        elif action == "type":
            text = kwargs.get("text", "")
            return self.type_text(text)

        elif action == "press":
            key = kwargs.get("key", "")
            return self.press_key(key)

        return ToolResult(status="FAILED", message=f"Unknown keyboard action: {action}")

    def hotkey(self, *keys) -> ToolResult:
        try:
            pyautogui.hotkey(*keys)
            return ToolResult(status="SUCCESS", message=f"Triggered hotkey: {' + '.join(keys)}")
        except Exception as e:
            return ToolResult(status="FAILED", message=f"Hotkey failed: {e}", error=str(e))

    def type_text(self, text: str) -> ToolResult:
        try:
            pyautogui.write(text, interval=0.01)
            return ToolResult(status="SUCCESS", message="Typed text successfully.")
        except Exception as e:
            return ToolResult(status="FAILED", message=f"Typing failed: {e}", error=str(e))

    def press_key(self, key: str) -> ToolResult:
        try:
            pyautogui.press(key)
            return ToolResult(status="SUCCESS", message=f"Pressed {key}.")
        except Exception as e:
            return ToolResult(status="FAILED", message=f"Key press failed: {e}", error=str(e))
