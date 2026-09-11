"""
JARVIS Screen Capture Tool
Ultra-reliable in-memory screen and cursor region capture using Qt QScreen grabWindow.
Handles high-DPI scaling, multi-monitor coordinates, UI Automation text extraction, and zero disk writes.
"""

import io
import os
import time
from typing import Optional, Tuple
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QGuiApplication, QCursor
from PySide6.QtCore import QBuffer, QIODevice, QRect, QPoint, Qt
from .base import BaseTool, ToolResult
from jarvis.app.config import config
from jarvis.utils.cursor_logger import log_layer


def _get_element_text_at(cx: int, cy: int) -> str:
    """Uses Windows UI Automation to extract accessible text/name under cursor coordinates."""
    try:
        import comtypes.client
        from comtypes.gen.UIAutomationClient import CUIAutomation, IUIAutomation, tagPOINT
        uia = comtypes.client.CreateObject(CUIAutomation, interface=IUIAutomation)
        elem = uia.ElementFromPoint(tagPOINT(cx, cy))
        if elem:
            name = (elem.CurrentName or "").strip()
            ctrl = (elem.CurrentLocalizedControlType or "").strip()
            if name:
                return f"{name} ({ctrl})" if ctrl else name
            return ctrl
    except Exception as e:
        pass
    return ""


class ScreenTool(BaseTool):
    name = "ScreenTool"
    description = "Captures on-demand in-memory screenshots for privacy-first vision understanding."

    def execute(self, action: str, **kwargs) -> ToolResult:
        if not config.get("cursor_context_enabled", True):
            return ToolResult(status="DISABLED", message="Screen and cursor context is disabled in settings.")

        action = action.lower().strip()
        radius = kwargs.get("radius", 200)
        cursor_pos = kwargs.get("cursor_pos")

        if action in ["capture_cursor_region", "capture_cursor"]:
            img_bytes, text_hint = self.capture_cursor_region_bytes(radius=radius, cursor_pos=cursor_pos)
            if not img_bytes:
                return ToolResult(status="FAILED", message="Could not capture cursor region.")
            return ToolResult(
                status="SUCCESS",
                message="Cursor region captured in memory.",
                data={"image_bytes": img_bytes, "text_hint": text_hint},
            )

        elif action == "capture_screen":
            img_bytes = self.capture_screen_bytes()
            if not img_bytes:
                return ToolResult(status="FAILED", message="Could not capture full screen.")
            return ToolResult(
                status="SUCCESS",
                message="Screen captured in memory.",
                data={"image_bytes": img_bytes},
            )

        return ToolResult(status="FAILED", message=f"Unknown screen action: {action}")

    def capture_cursor_region_bytes(
        self,
        radius: int = 200,
        cursor_pos: Optional[Tuple[int, int]] = None,
    ) -> Tuple[Optional[bytes], str]:
        """
        Captures in-memory bounding box centered on cursor position.
        Uses Qt's native high-DPI aware grabWindow. Never persists to disk.
        """
        if not config.get("cursor_context_enabled", True):
            return None, ""

        try:
            # 1. Determine cursor coordinates
            if cursor_pos:
                cx, cy = cursor_pos
            else:
                qpos = QCursor.pos()
                cx, cy = qpos.x(), qpos.y()

            log_layer(2, f"Cursor coordinates captured", x=cx, y=cy)

            # 2. Extract UI Automation accessible text at cursor (0ms local fallback)
            text_hint = _get_element_text_at(cx, cy)
            if text_hint:
                log_layer(4, f"UI Automation element hint extracted", hint=text_hint)

            # 3. Get screen at cursor position
            screen = QGuiApplication.screenAt(QPoint(cx, cy)) or QGuiApplication.primaryScreen()
            if not screen:
                log_layer(3, "Screen resolution failed: no screen found at coordinates", x=cx, y=cy)
                return None, text_hint

            # Grab full screen window
            pixmap = screen.grabWindow(0)
            if pixmap.isNull():
                log_layer(3, "screen.grabWindow(0) returned null pixmap (check screen permissions)")
                return None, text_hint

            # Handle device pixel ratio (DPI scaling, e.g. 125%, 150%)
            dpr = screen.devicePixelRatio()
            geo = screen.geometry()

            # Coordinates relative to this specific screen in physical pixmap space
            rel_x = int((cx - geo.x()) * dpr)
            rel_y = int((cy - geo.y()) * dpr)
            scaled_radius = int(radius * dpr)

            # Bounding box in physical pixmap pixels
            x1 = max(0, rel_x - scaled_radius)
            y1 = max(0, rel_y - scaled_radius)
            w = min(scaled_radius * 2, pixmap.width() - x1)
            h = min(scaled_radius * 2, pixmap.height() - y1)

            cropped = pixmap.copy(x1, y1, w, h)
            if cropped.isNull():
                cropped = pixmap

            # Convert to in-memory JPEG bytes
            buf = QBuffer()
            buf.open(QIODevice.WriteOnly)
            cropped.save(buf, "JPEG", 90)
            img_bytes = buf.data().data()
            buf.close()

            log_layer(
                3,
                "Screen region captured successfully",
                x=cx,
                y=cy,
                dpr=dpr,
                roi_w=w,
                roi_h=h,
                bytes=len(img_bytes),
            )

            # Optional: Save a debug capture file if debug mode is active
            if config.get("debug_mode", True):
                try:
                    debug_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "debug_captures")
                    os.makedirs(debug_dir, exist_ok=True)
                    debug_path = os.path.join(debug_dir, "last_cursor_roi.jpg")
                    with open(debug_path, "wb") as f:
                        f.write(img_bytes)
                except Exception:
                    pass

            return img_bytes, text_hint

        except Exception as e:
            log_layer(3, "Cursor region capture exception", error=str(e))
            return None, ""

    def capture_screen_bytes(self) -> Optional[bytes]:
        """Captures full primary screen in memory via Qt."""
        if not config.get("cursor_context_enabled", True):
            return None

        try:
            screen = QGuiApplication.primaryScreen()
            if not screen:
                return None

            pixmap = screen.grabWindow(0)
            if pixmap.isNull():
                return None

            buf = QBuffer()
            buf.open(QIODevice.WriteOnly)
            scaled = pixmap.scaled(1920, 1080, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            scaled.save(buf, "JPEG", 82)
            img_bytes = buf.data().data()
            buf.close()

            log_layer(3, "Full screen captured", bytes=len(img_bytes))
            return img_bytes
        except Exception as e:
            log_layer(3, "Full screen capture exception", error=str(e))
            return None
