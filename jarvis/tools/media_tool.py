"""
JARVIS Media Control Tool
Controls media playback (play/pause, next/previous track) using Win32 media keys.
"""

import win32api
import win32con
from .base import BaseTool, ToolResult


# Virtual key codes for media keys
VK_MEDIA_PLAY_PAUSE = 0xB3
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_STOP = 0xB2


class MediaTool(BaseTool):
    name = "MediaTool"
    description = "Controls media playback using system-wide media keys."

    def execute(self, action: str, **kwargs) -> ToolResult:
        action = action.lower().strip()

        if action == "play_pause":
            return self._send_media_key(VK_MEDIA_PLAY_PAUSE, "Toggled play/pause.")
        elif action == "next_track":
            return self._send_media_key(VK_MEDIA_NEXT_TRACK, "Skipped to next track.")
        elif action == "previous_track":
            return self._send_media_key(VK_MEDIA_PREV_TRACK, "Went to previous track.")
        elif action == "stop":
            return self._send_media_key(VK_MEDIA_STOP, "Stopped playback.")

        return ToolResult(status="FAILED", message=f"Unknown media action: {action}")

    def _send_media_key(self, vk_code: int, message: str) -> ToolResult:
        try:
            win32api.keybd_event(vk_code, 0, 0, 0)
            win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
            return ToolResult(status="SUCCESS", message=message)
        except Exception as e:
            return ToolResult(status="FAILED", message=f"Media control failed: {e}")
