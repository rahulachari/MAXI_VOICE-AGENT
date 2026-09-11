"""
JARVIS Context Engine
Maintains short-term conversational context and inspects active desktop environment.
"""

import time
from typing import Optional, Dict, Any
import pyautogui
from jarvis.ui.monitor_helper import get_active_window_info


class ContextEngine:
    def __init__(self, ttl_seconds: float = 60.0):
        self.ttl_seconds = ttl_seconds
        self._last_interaction_time: float = 0.0
        self._last_intent: Optional[str] = None
        self._last_target: Optional[str] = None
        self._conversation_state: Dict[str, Any] = {}
        self._pending_clarification: Optional[Dict[str, Any]] = None

    def set_pending_clarification(self, intent_dict: Dict[str, Any], missing_param: str, question: str):
        """Stores a pending action waiting for user clarification."""
        self._pending_clarification = {
            "intent_dict": intent_dict,
            "missing_param": missing_param,
            "question": question,
            "timestamp": time.time(),
        }

    def get_pending_clarification(self) -> Optional[Dict[str, Any]]:
        """Returns pending clarification if not timed out (within 60s)."""
        if not self._pending_clarification:
            return None
        if time.time() - self._pending_clarification.get("timestamp", 0) > 60.0:
            self._pending_clarification = None
            return None
        return self._pending_clarification

    def clear_pending_clarification(self):
        """Clears any pending clarification."""
        self._pending_clarification = None

    def get_desktop_context(self) -> Dict[str, Any]:
        """Collects minimal active foreground window and cursor state."""
        win_info = get_active_window_info()
        cx, cy = pyautogui.position()

        return {
            "window_title": win_info.get("title", ""),
            "process_name": win_info.get("process", ""),
            "hwnd": win_info.get("hwnd", 0),
            "cursor_pos": (cx, cy),
            "last_target": self.get_active_target(),
        }

    def update_interaction(self, intent: str, target: str, meta: Optional[Dict[str, Any]] = None):
        self._last_interaction_time = time.time()
        self._last_intent = intent
        self._last_target = target
        if meta:
            self._conversation_state.update(meta)

    def get_active_target(self) -> Optional[str]:
        if time.time() - self._last_interaction_time > self.ttl_seconds:
            # Context expired
            self._last_target = None
            self._conversation_state.clear()
        return self._last_target

    def clear(self):
        self._last_intent = None
        self._last_target = None
        self._conversation_state.clear()
        self._pending_clarification = None


# Global context singleton
context_engine = ContextEngine()
