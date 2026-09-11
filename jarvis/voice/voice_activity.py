"""
JARVIS Voice Activity Detection (VAD) & Audio Energy Metering
Tracks real-time microphone energy and detects speech boundaries (start & stop).
"""

import math
import numpy as np


class VoiceActivityDetector:
    def __init__(
        self,
        energy_threshold: float = 0.006,
        silence_duration_sec: float = 1.8,
        max_duration_sec: float = 45.0,
        sample_rate: int = 16000,
    ):
        self.energy_threshold = energy_threshold
        self.silence_duration_sec = silence_duration_sec
        self.max_duration_sec = max_duration_sec
        self.sample_rate = sample_rate

        self.speech_started = False
        self.silence_frames = 0
        self.total_frames = 0
        self.max_silence_frames = int(silence_duration_sec * (sample_rate / 1024))
        self.max_total_frames = int(max_duration_sec * (sample_rate / 1024))

    def reset(self):
        self.speech_started = False
        self.silence_frames = 0
        self.total_frames = 0

    def process_chunk(self, audio_data: np.ndarray) -> tuple[float, bool, bool]:
        """
        Processes an audio chunk (float32 or int16 numpy array).
        Returns: (normalized_energy, is_speech, is_finished)
          - normalized_energy: float from 0.0 to 1.0 (for HUD wave visualizer)
          - is_speech: True if current chunk is above silence threshold
          - is_finished: True if user spoke and then remained silent long enough, or timeout reached
        """
        if len(audio_data) == 0:
            return 0.0, False, False

        self.total_frames += 1

        # Calculate RMS energy
        if audio_data.dtype == np.int16:
            norm_audio = audio_data.astype(np.float32) / 32768.0
        else:
            norm_audio = audio_data.astype(np.float32)

        rms = float(np.sqrt(np.mean(norm_audio**2)))
        # Normalize energy to 0.0 - 1.0 scale with logarithmic scaling for visual punch
        normalized_energy = min(1.0, math.sqrt(max(0.0, rms * 10.0)))

        is_speech = rms > self.energy_threshold

        if is_speech:
            self.speech_started = True
            self.silence_frames = 0
        elif self.speech_started:
            self.silence_frames += 1

        # Finished if speech concluded with silence, or max duration reached
        is_finished = (
            (self.speech_started and self.silence_frames >= self.max_silence_frames)
            or (self.total_frames >= self.max_total_frames)
        )

        return normalized_energy, is_speech, is_finished
