"""
JARVIS High-Definition Neural Speech Engine
Smart female AI voice (en-US-AriaNeural) with professional prosody,
asynchronous worker playback, and instant barge-in / speech cancellation.
"""

import os
import re
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

# Definitive intelligent personal assistant voice (warm, natural, humanized female)
DEFAULT_NEURAL_VOICE = "en-US-JennyNeural"

# Available neural voices
AVAILABLE_VOICES = {
    "Lyra / Jenny (Studio Lady Voice, Warm & Natural)": "en-US-JennyNeural",
    "Aria (US, Professional Female)": "en-US-AriaNeural",
    "Sonia (UK, Elegant Female)": "en-GB-SoniaNeural",
    "Ava (US, Expressive Female)": "en-US-AvaNeural",
    "Brian (UK, Articulate Male)": "en-US-BrianNeural",
    "Guy (US, Natural Male)": "en-US-GuyNeural",
}

VOICE_MAP = {
    "lyra": "en-US-JennyNeural",
    "gemini": "en-US-JennyNeural",
    "gemini_lyra": "en-US-JennyNeural",
    "jenny": "en-US-JennyNeural",
    "aria": "en-US-AriaNeural",
    "sonia": "en-GB-SoniaNeural",
    "ava": "en-US-AvaNeural",
    "brian": "en-US-BrianNeural",
    "guy": "en-US-GuyNeural",
}


def clean_spoken_text(text: str) -> str:
    """Cleans text to make it natural and conversational for spoken output."""
    from jarvis.utils.text_cleaner import clean_spoken_text as _clean
    return _clean(text)


class TextToSpeechEngine:
    def __init__(self):
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._is_speaking = False
        self._current_thread: Optional[threading.Thread] = None
        self._lyra_cooldown_until = 0.0

        raw_v = str(config.get("voice_name", "lyra")).strip().lower()
        if "neural" in raw_v:
            self._voice = config.get("voice_name")
        else:
            self._voice = VOICE_MAP.get(raw_v, "lyra")

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

    def speak(self, text: str, on_start: Optional[Callable[[], None]] = None, on_finish: Optional[Callable[[], None]] = None):
        clean_text = clean_spoken_text(text)
        if not clean_text:
            if on_start:
                on_start()
            if on_finish:
                on_finish()
            return

        def _worker():
            with self._lock:
                try:
                    if pygame.mixer.get_init():
                        pygame.mixer.music.stop()
                        pygame.mixer.music.unload()
                except Exception:
                    pass

                self._stop_event.clear()
                self._is_speaking = True

                voice_choice = str(self._voice).lower()
                engine_pref = str(config.get("tts_engine", "neural")).lower()
                success = False

                # 1. Authentic Google Gemini Lyra Lady Voice (only if not on rate-limit cooldown)
                can_try_lyra = (
                    ("lyra" in voice_choice or engine_pref in ["lyra", "gemini_lyra", "gemini"])
                    and time.time() > self._lyra_cooldown_until
                )
                if can_try_lyra:
                    try:
                        success = self._speak_gemini_lyra(clean_text, on_start=on_start)
                    except Exception as e:
                        err_str = str(e)
                        if "429" in err_str or "quota" in err_str.lower():
                            print("[TTS] Gemini Lyra rate-limited (429). Fast switching to JennyNeural for session.")
                            self._lyra_cooldown_until = time.time() + 86400.0
                        else:
                            print(f"[TTS] Gemini Lyra synthesis error: {e}")
                            self._lyra_cooldown_until = time.time() + 1800.0
                        success = False

                # 2. High-definition natural neural female voice (Edge-TTS sentence-pipelined)
                if not success and not self._stop_event.is_set():
                    try:
                        target_voice = self._voice if ("lyra" not in voice_choice and "neural" in voice_choice) else "en-US-JennyNeural"
                        success = self._speak_neural(clean_text, voice=target_voice, on_start=on_start)
                    except Exception as e:
                        print(f"[TTS] Neural TTS failed: {e}")
                        success = False

                # 3. Offline SAPI5 as last resort only if completely offline
                if not success and not self._stop_event.is_set():
                    print("[TTS] Offline fallback: SAPI5 female voice...")
                    try:
                        self._speak_sapi5(clean_text, on_start=on_start)
                        success = True
                    except Exception as e:
                        print(f"[TTS] SAPI5 failed: {e}")

                self._is_speaking = False
                if on_finish and not self._stop_event.is_set():
                    on_finish()

        self._current_thread = threading.Thread(target=_worker, daemon=True)
        self._current_thread.start()

    def _speak_gemini_lyra(self, text: str, on_start: Optional[Callable[[], None]] = None) -> bool:
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
        if on_start and not self._stop_event.is_set():
            try:
                on_start()
            except Exception:
                pass

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

    def _speak_neural(self, text: str, voice: Optional[str] = None, on_start: Optional[Callable[[], None]] = None) -> bool:
        """Synthesizes speech using edge-tts with sentence-pipelined instant playback.
        Synthesizes the first sentence immediately (~200ms), starts audio playback right away,
        and pre-buffers subsequent sentences concurrently in background threads."""
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text.strip()) if s.strip()]
        if not sentences:
            return False

        chosen_voice = voice or self._voice
        if not chosen_voice or "lyra" in str(chosen_voice).lower() or "gemini" in str(chosen_voice).lower():
            chosen_voice = "en-US-JennyNeural"

        rate = config.get("tts_rate", 190)
        rate_percent = f"{int((rate - 180) / 1.8):+d}%"

        temp_files = []

        def _cleanup():
            for f in temp_files:
                _safe_cleanup(f)

        try:
            # Single sentence or short text: synthesize directly
            if len(sentences) == 1 or len(text.split()) < 22:
                temp_path = os.path.join(tempfile.gettempdir(), f"jarvis_speech_{int(time.time()*1000)}.mp3")
                temp_files.append(temp_path)

                async def _generate():
                    communicate = edge_tts.Communicate(text, chosen_voice, rate=rate_percent)
                    await communicate.save(temp_path)

                asyncio.run(_generate())

                if self._stop_event.is_set():
                    _cleanup()
                    return False

                if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
                    _cleanup()
                    return False

                pygame.mixer.music.load(temp_path)
                pygame.mixer.music.play()
                if on_start and not self._stop_event.is_set():
                    try:
                        on_start()
                    except Exception:
                        pass

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
                _cleanup()
                return True

            # Multi-sentence pipeline: synthesize Sentence 1 and start playing immediately
            import queue
            first_sentence_q = queue.Queue()

            def _synthesize_single(s_text, out_path, q_to_signal=None):
                try:
                    async def _run():
                        comm = edge_tts.Communicate(s_text, chosen_voice, rate=rate_percent)
                        await comm.save(out_path)
                    asyncio.run(_run())
                    if q_to_signal:
                        success = os.path.exists(out_path) and os.path.getsize(out_path) > 0
                        q_to_signal.put(success)
                except Exception as err:
                    print(f"[TTS Pipeline] Sentence synthesis failed: {err}")
                    if q_to_signal:
                        q_to_signal.put(False)

            # 1. Immediately launch background synthesis for all subsequent sentences in parallel
            remaining_paths = []
            for i, sent in enumerate(sentences[1:], start=1):
                pi = os.path.join(tempfile.gettempdir(), f"jarvis_chunk_{i}_{int(time.time()*1000)}.mp3")
                temp_files.append(pi)
                t = threading.Thread(target=_synthesize_single, args=(sent, pi, None), daemon=True)
                t.start()
                remaining_paths.append(pi)

            # 2. Synthesize sentence 0 first to produce sound ASAP!
            p0 = os.path.join(tempfile.gettempdir(), f"jarvis_chunk_0_{int(time.time()*1000)}.mp3")
            temp_files.append(p0)
            _synthesize_single(sentences[0], p0, first_sentence_q)

            try:
                s0_ok = first_sentence_q.get(timeout=3.5)
            except Exception:
                s0_ok = False

            if not s0_ok or self._stop_event.is_set():
                _cleanup()
                return False

            # Start playback of Sentence 0 immediately!
            pygame.mixer.music.load(p0)
            pygame.mixer.music.play()
            if on_start and not self._stop_event.is_set():
                try:
                    on_start()
                except Exception:
                    pass

            # 3. Seamlessly play subsequent sentences as each finishes
            for pi in remaining_paths:
                while pygame.mixer.music.get_busy():
                    if self._stop_event.is_set():
                        pygame.mixer.music.stop()
                        pygame.mixer.music.unload()
                        _cleanup()
                        return False
                    time.sleep(0.02)

                if self._stop_event.is_set():
                    _cleanup()
                    return False

                # Ensure next sentence audio is saved (already synthesizing in background)
                wait_start = time.time()
                while (not os.path.exists(pi) or os.path.getsize(pi) == 0) and (time.time() - wait_start < 4.0):
                    if self._stop_event.is_set():
                        _cleanup()
                        return False
                    time.sleep(0.02)

                if os.path.exists(pi) and os.path.getsize(pi) > 0 and not self._stop_event.is_set():
                    try:
                        pygame.mixer.music.unload()
                    except Exception:
                        pass
                    pygame.mixer.music.load(pi)
                    pygame.mixer.music.play()

            # Wait for final sentence playback to conclude
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
            _cleanup()
            return True

        except Exception as e:
            print(f"[TTS Pipeline] Error: {e}")
            _cleanup()
            return False

    def _speak_sapi5(self, text: str, on_start: Optional[Callable[[], None]] = None):
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

            if on_start and not self._stop_event.is_set():
                try:
                    on_start()
                except Exception:
                    pass

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
