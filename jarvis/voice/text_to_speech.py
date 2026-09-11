"""
JARVIS High-Definition Neural Speech Engine
Smart female AI voice (en-US-AriaNeural) with professional prosody,
asynchronous worker playback, and instant barge-in / speech cancellation.
"""

import os
import asyncio
import tempfile
import threading
import time
from typing import Optional, Callable
import edge_tts
import pygame
import pyttsx3
import pythoncom
from jarvis.app.config import config

# Initialize pygame mixer for audio playback
try:
    pygame.mixer.init()
except Exception as e:
    print(f"[TTS] Pygame mixer init: {e}")

# Smart, clear UK female voice — elegant and articulate
DEFAULT_NEURAL_VOICE = "en-GB-SoniaNeural"

# Available female neural voices (user can switch in settings)
AVAILABLE_VOICES = {
    "Aria (US, Professional)": "en-US-AriaNeural",
    "Jenny (US, Friendly)": "en-US-JennyNeural",
    "Michelle (US, Warm)": "en-US-MichelleNeural",
    "Sonia (UK, Elegant)": "en-GB-SoniaNeural",
    "Libby (UK, Clear)": "en-GB-LibbyNeural",
    "Natasha (AU, Smart)": "en-AU-NatashaNeural",
    "Brian (US, Male)": "en-US-BrianNeural",
}


class TextToSpeechEngine:
    def __init__(self):
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._is_speaking = False
        self._current_thread: Optional[threading.Thread] = None
        self._voice = config.get("voice_name") or DEFAULT_NEURAL_VOICE

    def is_speaking(self) -> bool:
        return self._is_speaking

    def stop(self):
        """Barge-in: Immediately halts any ongoing speech playback."""
        self._stop_event.set()
        try:
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
        except Exception:
            pass
        self._is_speaking = False

    def speak(self, text: str, on_finish: Optional[Callable[[], None]] = None):
        if not text or not text.strip():
            if on_finish:
                on_finish()
            return

        def _worker():
            with self._lock:
                # Force an extra stop just in case
                try:
                    if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                        pygame.mixer.music.stop()
                        pygame.mixer.music.unload()
                except Exception:
                    pass

                self._stop_event.clear()
                self._is_speaking = True
                
                success = False
                # 1. Try high-definition neural voice first
                try:
                    success = self._speak_neural(text)
                except Exception as e:
                    print(f"[TTS] Neural TTS failed, falling back to SAPI5: {e}")

                # 2. Fallback to offline SAPI5 if neural fails or offline
                if not success and not self._stop_event.is_set():
                    self._speak_sapi5(text)

                self._is_speaking = False
                if on_finish and not self._stop_event.is_set():
                    on_finish()

        self._current_thread = threading.Thread(target=_worker, daemon=True)
        self._current_thread.start()

    def _speak_neural(self, text: str) -> bool:
        """Synthesizes speech using edge-tts AriaNeural and plays via pygame mixer."""
        temp_path = os.path.join(tempfile.gettempdir(), f"jarvis_speech_{int(time.time()*1000)}.mp3")

        async def _generate():
            voice = self._voice
            rate = config.get("tts_rate", 190)
            # Map rate: 190 → +5% (slightly faster for smart/professional tone)
            rate_percent = f"{int((rate - 180) / 1.8):+d}%"

            # Build SSML for professional prosody when using Aria
            if "Aria" in voice or "Jenny" in voice or "Sonia" in voice:
                # Use SSML for natural pitch and contour
                ssml = f"""<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'>
                    <voice name='{voice}'>
                        <prosody rate='{rate_percent}' pitch='+2%' volume='+5%'>
                            {_escape_ssml(text)}
                        </prosody>
                    </voice>
                </speak>"""
                communicate = edge_tts.Communicate(ssml, voice)
            else:
                communicate = edge_tts.Communicate(text, voice, rate=rate_percent)

            await communicate.save(temp_path)

        asyncio.run(_generate())

        if self._stop_event.is_set():
            _safe_cleanup(temp_path)
            return False

        if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
            return False

        pygame.mixer.music.load(temp_path)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            if self._stop_event.is_set():
                pygame.mixer.music.stop()
                break
            time.sleep(0.04)

        try:
            pygame.mixer.music.unload()
        except Exception:
            pass
        _safe_cleanup(temp_path)

        return True

    def _speak_sapi5(self, text: str):
        """Offline fallback using Windows SAPI5 with female voice preference."""
        pythoncom.CoInitialize()
        try:
            engine = pyttsx3.init()
            rate = config.get("tts_rate", 190)
            volume = config.get("tts_volume", 1.0)
            engine.setProperty("rate", rate)
            engine.setProperty("volume", volume)

            # Try to select a female SAPI5 voice
            voices = engine.getProperty("voices")
            for v in voices:
                if "zira" in v.name.lower() or "female" in v.name.lower():
                    engine.setProperty("voice", v.id)
                    break

            # Smart sentence splitting: preserve ? and ! for natural intonation
            import re
            sentences = re.split(r'(?<=[.!?])\s+', text)
            for s in sentences:
                s = s.strip()
                if not s or self._stop_event.is_set():
                    break
                engine.say(s)
                engine.runAndWait()
        except Exception as e:
            print(f"[TTS SAPI5] Error: {e}")
        finally:
            pythoncom.CoUninitialize()


def _escape_ssml(text: str) -> str:
    """Escapes special XML characters for SSML."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def _safe_cleanup(path: str):
    """Safely removes a temporary file."""
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


# Global Singleton
tts_engine = TextToSpeechEngine()
TextToSpeechProvider = TextToSpeechEngine
