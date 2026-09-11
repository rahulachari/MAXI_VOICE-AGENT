"""
JARVIS Speech-To-Text Provider Architecture
Supports Groq Whisper-large-v3-turbo (ultra-fast sub-second transcription) and Google Speech (offline/free fallback).
"""

import io
import os
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


def pcm_to_wav_bytes(audio_data: np.ndarray, sample_rate: int = 16000) -> bytes:
    """Converts numpy int16 array to in-memory WAV file bytes."""
    if audio_data.dtype != np.int16:
        # Convert float32 to int16
        audio_int16 = (audio_data * 32767).clip(-32768, 32767).astype(np.int16)
    else:
        audio_int16 = audio_data

    byte_io = io.BytesIO()
    with wave.open(byte_io, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_int16.tobytes())
    return byte_io.getvalue()


class GoogleSTT(SpeechToTextProvider):
    def __init__(self):
        self.recognizer = sr.Recognizer()

    def transcribe(self, audio_data: np.ndarray, sample_rate: int = 16000) -> str:
        wav_bytes = pcm_to_wav_bytes(audio_data, sample_rate)
        byte_io = io.BytesIO(wav_bytes)

        with sr.AudioFile(byte_io) as source:
            audio = self.recognizer.record(source)

        try:
            text = self.recognizer.recognize_google(audio)
            return text.strip()
        except sr.UnknownValueError:
            return ""
        except sr.RequestError as e:
            print(f"[GoogleSTT] Request error: {e}")
            return ""


def get_stt_provider() -> SpeechToTextProvider:
    return GoogleSTT()

