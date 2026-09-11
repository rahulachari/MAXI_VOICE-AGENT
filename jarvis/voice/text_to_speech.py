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


def clean_spoken_text(text: str) -> str:
    """Cleans text to make it natural and conversational for spoken output."""
    if not text:
        return ""

    import re
    # If text is raw JSON, extract spoken_response or message
    if text.strip().startswith("{") and text.strip().endswith("}"):
        try:
            import json
            data = json.loads(text)
            text = data.get("spoken_response") or data.get("message") or data.get("answer") or ""
        except Exception:
            m = re.search(r'"spoken_response":\s*"([^"]+)"', text)
            if m:
                text = m.group(1)
            else:
                text = re.sub(r'[\{\}\[\]"\'\\]', '', text)
                text = re.sub(r'(category|action|target|params):', '', text)

    # Strip code blocks and markdown symbols
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    text = re.sub(r'[*_#~>|]', '', text)
    text = re.sub(r'https?://\S+', 'link', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


class TextToSpeechEngine:
    def __init__(self):
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._is_speaking = False
        self._current_thread: Optional[threading.Thread] = None
        self._voice = config.get("voice_name") or DEFAULT_NEURAL_VOICE
        self._sapi5_engine = None

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
        if self._sapi5_engine:
            try:
                self._sapi5_engine.stop()
            except Exception:
                pass
        self._is_speaking = False

    def speak(self, text: str, on_finish: Optional[Callable[[], None]] = None):
        clean_text = clean_spoken_text(text)
        if not clean_text:
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
                # 1. Try Google Gemini Lyra voice first
                if config.get("gemini_api_key"):
                    try:
                        success = self._speak_gemini_lyra(clean_text)
                    except Exception as e:
                        print(f"[TTS] Gemini Lyra TTS failed, falling back to neural: {e}")

                # 2. Fallback to high-definition edge neural voice
                if not success and not self._stop_event.is_set():
                    try:
                        success = self._speak_neural(clean_text)
                    except Exception as e:
                        print(f"[TTS] Neural TTS failed, falling back to SAPI5: {e}")

                # 3. Fallback to offline SAPI5 if neural fails and stop was not requested
                if not success and not self._stop_event.is_set():
                    self._speak_sapi5(clean_text)

                self._is_speaking = False
                if on_finish and not self._stop_event.is_set():
                    on_finish()

        self._current_thread = threading.Thread(target=_worker, daemon=True)
        self._current_thread.start()

    def _speak_gemini_lyra(self, text: str) -> bool:
        """Synthesizes speech using Google Gemini Lyra voice and plays via pygame mixer."""
        gemini_key = config.get("gemini_api_key")
        if not gemini_key:
            return False

        temp_wav = os.path.join(tempfile.gettempdir(), f"jarvis_lyra_{int(time.time()*1000)}.wav")
        import urllib.request
        import base64
        import wave
        import json

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-tts-preview:generateContent?key={gemini_key}"
        payload = {
            "contents": [{"parts": [{"text": text}]}],
            "generationConfig": {
                "response_modalities": ["AUDIO"],
                "speech_config": {
                    "voice_config": {
                        "prebuilt_voice_config": {
                            "voice_name": "Lyra"
                        }
                    }
                }
            }
        }
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            candidates = data.get("candidates", [])
            if not candidates:
                return False
            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                return False
            inline_data = parts[0].get("inlineData", {})
            b64_audio = inline_data.get("data")
            if not b64_audio:
                return False
            raw_pcm = base64.b64decode(b64_audio)

        if self._stop_event.is_set():
            return False

        with wave.open(temp_wav, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(24000)
            wf.writeframes(raw_pcm)

        if self._stop_event.is_set():
            _safe_cleanup(temp_wav)
            return False

        pygame.mixer.music.load(temp_wav)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            if self._stop_event.is_set():
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
                break
            time.sleep(0.02)

        try:
            pygame.mixer.music.unload()
        except Exception:
            pass
        _safe_cleanup(temp_wav)
        return True

    def _speak_neural(self, text: str) -> bool:
        """Synthesizes speech using edge-tts and plays via pygame mixer."""
        temp_path = os.path.join(tempfile.gettempdir(), f"jarvis_speech_{int(time.time()*1000)}.mp3")

        async def _generate():
            voice = self._voice
            rate = config.get("tts_rate", 190)
            # Map rate: 190 → +5% (slightly faster for smart/professional tone)
            rate_percent = f"{int((rate - 180) / 1.8):+d}%"
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
                pygame.mixer.music.unload()
                break
            time.sleep(0.02)

        try:
            pygame.mixer.music.unload()
        except Exception:
            pass
        _safe_cleanup(temp_path)

        return True

    def _speak_sapi5(self, text: str):
        """Offline fallback using Windows SAPI5 with female voice preference."""
        if self._stop_event.is_set():
            return

        pythoncom.CoInitialize()
        try:
            engine = pyttsx3.init()
            self._sapi5_engine = engine
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
