"""
JARVIS Cursor & Vision Pipeline Logger
Maintains persistent, local-only diagnostic logging for all 5 layers of the
'Point Anywhere on Screen' feature, gated behind the debug_mode flag.
"""

import os
import time
from datetime import datetime
from jarvis.app.config import config

LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cursor_debug.log")


def log_layer(layer: int, message: str, **kwargs):
    """
    Logs diagnostic info for one of the 5 layers:
    - Layer 1: Hotkey capture
    - Layer 2: Cursor position capture
    - Layer 3: Screen / region capture
    - Layer 4: Content extraction (Vision / OCR / UIAutomation)
    - Layer 5: Context injection into command
    """
    if not config.get("debug_mode", True):
        return

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    extra = " | ".join(f"{k}={v}" for k, v in kwargs.items()) if kwargs else ""
    log_line = f"[{timestamp}] [Layer {layer}] {message}"
    if extra:
        log_line += f" | {extra}"

    # Print to console for immediate visibility
    print(log_line)

    # Append to persistent local file
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_line + "\n")
    except Exception:
        pass
