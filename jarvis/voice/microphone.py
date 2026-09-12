"""
JARVIS Microphone Stream Manager
Captures audio via sounddevice, streams real-time energy levels to UI, and triggers VAD cutoff.
"""

import threading
import numpy as np
import sounddevice as sd
from typing import Callable, Optional
from .voice_activity import VoiceActivityDetector


class MicrophoneRecorder:
    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        energy_callback: Optional[Callable[[float], None]] = None,
        finished_callback: Optional[Callable[[np.ndarray], None]] = None,
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.energy_callback = energy_callback
        self.finished_callback = finished_callback

        self.vad = VoiceActivityDetector(sample_rate=sample_rate)
        self.is_recording = False
        self._stream: Optional[sd.InputStream] = None
        self._audio_frames: list[np.ndarray] = []
        self.push_to_talk = False
        self._lock = threading.Lock()

    def start_listening(self, push_to_talk: bool = False):
        with self._lock:
            if self.is_recording:
                return

            self.push_to_talk = push_to_talk
            self._audio_frames = []
            self.vad.reset()
            self.is_recording = True

            try:
                self._stream = sd.InputStream(
                    samplerate=self.sample_rate,
                    channels=self.channels,
                    dtype="int16",
                    blocksize=1024,
                    callback=self._audio_callback,
                )
                self._stream.start()
            except Exception as e:
                print(f"[Mic] Failed to open audio stream: {e}")
                self.is_recording = False

    def _audio_callback(self, indata, frames, time_info, status):
        if not self.is_recording:
            return

        chunk = indata.copy().flatten()
        self._audio_frames.append(chunk)

        # Process VAD
        energy, is_speech, is_finished = self.vad.process_chunk(chunk)

        if self.energy_callback:
            self.energy_callback(energy)

        # In push-to-talk mode, only key release triggers finish
        if is_finished and not self.push_to_talk:
            # Silence detected after speech in hands-free mode: complete recording
            threading.Thread(target=self.stop_listening, daemon=True).start()

    def stop_listening(self) -> Optional[np.ndarray]:
        with self._lock:
            if not self.is_recording:
                return None

            self.is_recording = False
            if self._stream:
                try:
                    self._stream.stop()
                    self._stream.close()
                except Exception as e:
                    print(f"[Mic] Error closing stream: {e}")
                self._stream = None

            if self._audio_frames:
                full_audio = np.concatenate(self._audio_frames, axis=0)
            else:
                full_audio = np.array([], dtype=np.int16)

        if self.finished_callback:
            self.finished_callback(full_audio)

        return full_audio
