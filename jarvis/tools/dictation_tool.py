"""
JARVIS Dictation Tool
Clones VoiceOS Dictation Mode: Types polished text into the active Windows application,
automatically cleaning filler words, fixing capitalization, and handling self-corrections.
"""

import re
import time
import pyperclip
import pyautogui
from .base import BaseTool, ToolResult

FILLER_WORDS = [
    r"\bum+\b",
    r"\buh+\b",
    r"\ber+\b",
    r"\bah+\b",
    r"\blike\b",
    r"\byou\s+know\b",
]


def clean_dictated_text(raw_text: str) -> str:
    text = raw_text.strip()
    # Remove filler words
    for pattern in FILLER_WORDS:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    # Clean double spaces
    text = re.sub(r"\s+", " ", text).strip()

    # Self-correction handling: e.g. "actually I mean tomorrow" -> "tomorrow"
    if "actually i mean" in text.lower():
        parts = re.split(r"actually\s+i\s+mean", text, flags=re.IGNORECASE)
        text = parts[-1].strip()

    # Ensure capitalized start
    if text and len(text) > 0:
        text = text[0].upper() + text[1:]

    return text


class DictationTool(BaseTool):
    name = "DictationTool"
    description = "Types polished dictated text into the active foreground window."

    def execute(self, action: str, **kwargs) -> ToolResult:
        raw_text = kwargs.get("text", "")
        if not raw_text:
            return ToolResult(status="FAILED", message="No speech detected to dictate.")

        polished = clean_dictated_text(raw_text)

        try:
            # Use clipboard paste for fast, character-safe Unicode insertion
            old_clip = pyperclip.paste()
            pyperclip.copy(polished + " ")
            time.sleep(0.05)
            pyautogui.hotkey("ctrl", "v")
            time.sleep(0.05)
            # Restore clipboard asynchronously
            pyperclip.copy(old_clip)

            return ToolResult(
                status="SUCCESS",
                message="Dictated.",
                data={"text": polished},
            )
        except Exception as e:
            return ToolResult(status="FAILED", message=f"Dictation failed: {e}", error=str(e))
