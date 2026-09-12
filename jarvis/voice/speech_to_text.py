"""
JARVIS Speech-To-Text Provider Architecture
Supports Groq Whisper-large-v3-turbo (ultra-fast sub-second transcription) and Google Speech (offline/free fallback).
"""

import io
import re
import wave
from abc import ABC, abstractmethod
import numpy as np
import speech_recognition as sr
from jarvis.app.config import config


class SpeechToTextProvider(ABC):
    @abstractmethod
    def transcribe(self, audio_data: np.ndarray, sample_rate: int = 16000) -> str:
        """Transcribes raw PCM audio data into text."""
        pass


CUSTOM_VOCABULARY_BOOSTS = [
    # LinkedIn corrections (e.g. user reports "open Linkedin" misheard as "open linked")
    (r"\b(open|goto|go\s+to|launch|find|search)\s+(linked|link\s*in|linking|linkdin|link\s*then)\b", r"\1 LinkedIn"),
    (r"\b(linked\s*in|linkdin|linking|link\s*then)\b", "LinkedIn"),
    (r"\b(his|her|their)?\s*linked\s*profile\b", r"\1 LinkedIn profile"),

    # Music & Artists
    (r"\b(hang\s*over)\b", "Hangover"),
    (r"\b(d\s*c|desi\s*crew|d\.c\.)\b", "DC"),
    (r"\b(spotty\s*fi|spotifly)\b", "Spotify"),

    # Everyday apps & services
    (r"\b(g\s*mail|g\s*meil|gee\s*mail|jeemail|jimail)\b", "Gmail"),
    (r"\b(git\s*hub|get\s*hub)\b", "GitHub"),
    (r"\b(resumay|resumee|rezume|rezumay)\b", "resume"),
    (r"\b(apply\s+for\s+this|apply\s+for\s+the\s+job|apply\s+to\s+this|apply\s+job)\b", "apply for this job"),
    (r"\b(you\s*tube|u\s*tube|ytube)\b", "YouTube"),
    (r"\b(whats\s*app|what\s*app)\b", "WhatsApp"),
    (r"\b(poke\s*games)\b", "Poki games"),
    (r"\b(visual\s*studio\s*code|vs\s*code)\b", "VS Code"),
    (r"\b(task\s*manager|task\s*mgr)\b", "Task Manager"),
    (r"\b(power\s*point)\b", "PowerPoint"),

    # Calendar & Reminders
    (r"\b(calender)\b", "calendar"),
    (r"\b(rashan|ration\s*card)\b", "ration"),
]


def post_process_transcript(text: str) -> str:
    """Corrects common voice transcription homophones, names, and boosts domain phrases."""
    if not text:
        return ""

    t = text.strip()

    # 1. Assistant name homophones
    t = re.sub(r"\b(java|service|harvest|travis|charvis|jarviss|javis)\b", "Jarvis", t, flags=re.IGNORECASE)

    # 2. Weather vs Whether correction
    t = re.sub(r"\bthe\s+whether\b", "the weather", t, flags=re.IGNORECASE)
    t = re.sub(r"\bwhether\s+(in|for|today|tomorrow|outside|forecast|report|condition|update)\b",
               lambda m: f"weather {m.group(1)}", t, flags=re.IGNORECASE)
    if any(w in t.lower() for w in ["temperature", "rain", "forecast", "degrees", "celsius", "climate", "outside"]):
        t = re.sub(r"\bwhether\b", "weather", t, flags=re.IGNORECASE)

    # 3. Apply custom vocabulary phrase boosting
    for pattern, replacement in CUSTOM_VOCABULARY_BOOSTS:
        t = re.sub(pattern, replacement, t, flags=re.IGNORECASE)

    # 4. Strip filler words from the front of commands (e.g. "um open calendar" -> "open calendar")
    t = re.sub(r"^(um+|uh+|er+|ah+|please)\s+", "", t, flags=re.IGNORECASE)

    return t.strip()


def pcm_to_wav_bytes(audio_data: np.ndarray, sample_rate: int = 16000) -> bytes:
    """
    Normalizes audio gain, applies soft noise gate, eliminates DC offset,
    and converts numpy array to high-clarity 16-bit PCM WAV.
    """
    if audio_data is None or len(audio_data) == 0:
        return b""

    # Convert to float32 for signal processing
    if audio_data.dtype == np.int16:
        float_audio = audio_data.astype(np.float32) / 32768.0
    else:
        float_audio = audio_data.astype(np.float32)

    # 1. Remove DC bias (center waveform at zero)
    float_audio = float_audio - np.mean(float_audio)

    # 2. Soft noise gate: damp stationary microphone hiss below subtle threshold
    noise_threshold = 0.003
    mask = np.abs(float_audio) < noise_threshold
    float_audio[mask] *= 0.3

    # 3. Peak normalization with headroom for quiet inputs
    peak = np.max(np.abs(float_audio))
    if peak > 0.005:
        gain = min(0.92 / peak, 5.0)
        float_audio = float_audio * gain

    # 4. Clip safely and quantize back to 16-bit PCM
    audio_int16 = (float_audio * 32767).clip(-32768, 32767).astype(np.int16)

    byte_io = io.BytesIO()
    with wave.open(byte_io, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_int16.tobytes())
    return byte_io.getvalue()


def _log_stt_interaction(raw_text: str, processed_text: str, locale: str):
    """Local-only debug logging for transcription accuracy auditing (zero audio stored)."""
    try:
        from datetime import datetime
        from jarvis.storage.database import get_data_dir

        log_file = get_data_dir() / "stt_audit.log"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] [{locale}] RAW: '{raw_text}' -> PROCESSED: '{processed_text}'\n")
    except Exception:
        pass


class GoogleSTT(SpeechToTextProvider):
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.energy_threshold = 280
        self.recognizer.pause_threshold = 0.8

    def transcribe(self, audio_data: np.ndarray, sample_rate: int = 16000) -> str:
        if audio_data is None or len(audio_data) == 0:
            return ""

        wav_bytes = pcm_to_wav_bytes(audio_data, sample_rate)
        if not wav_bytes:
            return ""

        byte_io = io.BytesIO(wav_bytes)

        try:
            with sr.AudioFile(byte_io) as source:
                audio = self.recognizer.record(source)
        except Exception as e:
            print(f"[GoogleSTT] Failed to record from audio buffer: {e}")
            return ""

        # Multi-locale recognition: handles both Indian English and US English accents smoothly
        locales = ["en-IN", "en-US"]
        for loc in locales:
            try:
                raw_text = self.recognizer.recognize_google(audio, language=loc)
                if raw_text and raw_text.strip():
                    processed = post_process_transcript(raw_text.strip())
                    _log_stt_interaction(raw_text, processed, loc)
                    return processed
            except sr.UnknownValueError:
                continue
            except sr.RequestError as e:
                print(f"[GoogleSTT] Request error with {loc}: {e}")
                continue

        return ""


def get_stt_provider() -> SpeechToTextProvider:
    return GoogleSTT()


