"""
JARVIS Configuration Manager
Loads settings from %LOCALAPPDATA%/JARVIS/settings.json, environment variables, and defaults.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict
from dotenv import load_dotenv
from jarvis.storage.database import get_data_dir

# Load .env if present
load_dotenv()


DEFAULT_CONFIG: Dict[str, Any] = {
    "activation_hotkey": "ctrl+alt",
    "history_hotkey": "ctrl+alt+h",
    "ai_provider": os.getenv("AI_PROVIDER", "groq"),
    "ai_model": os.getenv("AI_MODEL", "openai/gpt-oss-120b"),
    "groq_api_key": os.getenv("GROQ_API_KEY", ""),
    "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
    "gemini_api_key": os.getenv("GEMINI_API_KEY", ""),
    "stt_provider": "groq_whisper" if os.getenv("GROQ_API_KEY") else "google",
    "tts_engine": "sapi5",
    "tts_rate": int(os.getenv("VOICE_RATE", "190")),
    "tts_volume": float(os.getenv("VOICE_VOLUME", "1.0")),
    "voice_name": "en-GB-SoniaNeural",
    "save_history": True,
    "confirm_destructive": True,
    "active_mode": "agent",  # 'agent', 'dictation', 'edit'
    "sound_effects": True,
    "notch_always_visible": False,
    "memory_enabled": True,
    "calendar_default_duration": 30,
    "task_notifications": True,
}


class ConfigManager:
    def __init__(self, config_path: Path = None):
        self.config_path = config_path or (get_data_dir() / "settings.json")
        self._config: Dict[str, Any] = DEFAULT_CONFIG.copy()
        self.load()

    def load(self):
        """Loads configuration from JSON file, keeping defaults for missing keys."""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    self._config.update(saved)
            except Exception as e:
                print(f"[Config] Error loading settings.json: {e}")

        # Always ensure environment variables take priority for keys if not set in JSON
        if not self._config.get("groq_api_key") and os.getenv("GROQ_API_KEY"):
            self._config["groq_api_key"] = os.getenv("GROQ_API_KEY")

        if self._config.get("groq_api_key") and self._config.get("stt_provider") == "google":
            self._config["stt_provider"] = "groq_whisper"

    def save(self):
        """Saves current configuration to JSON file."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Config] Error saving settings.json: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def set(self, key: str, value: Any, auto_save: bool = True):
        self._config[key] = value
        if auto_save:
            self.save()

    def all(self) -> Dict[str, Any]:
        return self._config.copy()


config = ConfigManager()
