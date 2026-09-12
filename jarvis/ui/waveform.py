"""
JARVIS Siri & Gemini Live Dynamic Waveform Engine
High-performance 60 FPS procedural audio-reactive fluid wave visualizer.
Features multi-harmonic sinusoidal blending, iridescent chromatic gradients,
and organic amplitude modulation driven by live microphone energy.
"""

import math
import time
from PySide6.QtCore import Qt, QTimer, QPointF
from PySide6.QtGui import QPainter, QPainterPath, QColor, QLinearGradient, QBrush, QPen
from PySide6.QtWidgets import QWidget


class SiriWaveformWidget(QWidget):
    """
    Siri & Gemini Live fluid waveform visualizer.
    Renders 4 overlapping iridescent luminous harmonic waves that bubble
    and surge in real time with voice audio energy.
    """

    def __init__(self, parent=None, height: int = 34):
        super().__init__(parent)
        self.setFixedHeight(height)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)

        self._state = "IDLE"  # IDLE, LISTENING, PROCESSING, SPEAKING, ERROR
        self._energy = 0.05
        self._target_energy = 0.05
        self._phase = 0.0
        self._phase_speaking = 0.0

        # Layer parameters: (freq, speed, base_amp, colors, stroke)
        self._layers = [
            {
                "freq": 0.022,
                "speed": 2.4,
                "base_amp": 0.35,
                "colors": [(0.0, QColor(0, 242, 254, 210)), (1.0, QColor(79, 172, 254, 180))],
                "stroke": QColor(0, 242, 254, 230),
            },
            {
                "freq": 0.035,
                "speed": -3.1,
                "base_amp": 0.28,
                "colors": [(0.0, QColor(178, 36, 239, 180)), (1.0, QColor(117, 121, 255, 160))],
                "stroke": QColor(178, 36, 239, 210),
            },
            {
                "freq": 0.016,
                "speed": 1.7,
                "base_amp": 0.42,
                "colors": [(0.0, QColor(0, 198, 255, 170)), (1.0, QColor(0, 114, 255, 150))],
                "stroke": QColor(0, 198, 255, 200),
            },
            {
                "freq": 0.045,
                "speed": -2.0,
                "base_amp": 0.22,
                "colors": [(0.0, QColor(240, 147, 251, 150)), (1.0, QColor(245, 87, 108, 130))],
                "stroke": QColor(240, 147, 251, 180),
            },
        ]

        # 60 FPS animation timer
        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start()

    def set_state(self, state: str):
        self._state = (state or "IDLE").upper()
        if self._state == "IDLE":
            self._target_energy = 0.06
        elif self._state in ["PROCESSING", "THINKING"]:
            self._target_energy = 0.45
        elif self._state in ["SPEAKING"]:
            self._target_energy = 0.65
        self.update()

    def set_energy(self, energy: float):
        """Called by audio engine with normalized volume [0.0, 1.0]."""
        e = max(0.0, min(1.0, energy))
        # Boost quiet voices for visible bubbling waves
        boosted = math.pow(e, 0.6) * 1.3
        self._target_energy = max(0.08, min(1.0, boosted))

    def _on_tick(self):
        # Smooth exponential easing for fluid responsiveness
        self._energy += (self._target_energy - self._energy) * 0.18

        # In speaking mode, generate natural undulating rhythm
        if self._state == "SPEAKING":
            self._phase_speaking += 0.09
            cadence = 0.35 + 0.35 * (math.sin(self._phase_speaking * 2.2) * 0.5 + 0.5)
            self._energy = 0.3 + cadence * 0.5
        elif self._state in ["PROCESSING", "THINKING"]:
            self._phase += 0.08
        else:
            self._phase += 0.035

        self.update()

    def paintEvent(self, event):
        w = self.width()
        h = self.height()
        if w <= 0 or h <= 0:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        mid_y = h / 2.0
        max_wave_height = (h / 2.0) * 0.92

        # Draw each harmonic fluid wave layer with Siri/Gemini glow
        for idx, layer in enumerate(self._layers):
            freq = layer["freq"]
            speed = layer["speed"]
            base_amp = layer["base_amp"]
            phase_offset = self._phase * speed + (idx * 1.57)

            # Modulate amplitude with voice energy
            amp = max_wave_height * (base_amp * 0.3 + self._energy * base_amp * 1.7)
            if self._state == "IDLE":
                amp = max_wave_height * 0.12 * (0.8 + 0.2 * math.sin(self._phase * 1.5 + idx))

            # Build smooth curve across widget width
            path = QPainterPath()
            path.moveTo(0, mid_y)

            # Sample every 4 pixels for silky smoothness
            step = 4
            for x in range(0, w + step, step):
                # Window function (Hanning bell curve) so wave gracefully tapers at left/right edges
                envelope = math.sin((x / w) * math.pi)
                # Harmonic wave equation with primary + secondary overtone
                y_disp = (
                    math.sin(x * freq + phase_offset) * 0.75
                    + math.sin(x * freq * 1.6 - phase_offset * 0.6) * 0.25
                ) * amp * envelope
                path.lineTo(x, mid_y + y_disp)

            # Close path along center to create a radiant liquid ribbon
            path.lineTo(w, mid_y)
            path.lineTo(0, mid_y)
            path.closeSubpath()

            # Create vibrant Siri iridescent gradient
            grad = QLinearGradient(0, 0, w, 0)
            for stop, color in layer["colors"]:
                col = QColor(color)
                alpha = int(color.alpha() * (0.6 + self._energy * 0.4))
                col.setAlpha(min(255, alpha))
                grad.setColorAt(stop, col)

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(grad))
            painter.drawPath(path)

            # Luminous crest stroke
            stroke_pen = QPen(layer["stroke"], 1.4)
            painter.setPen(stroke_pen)
            painter.setBrush(Qt.NoBrush)

            # Draw the top contour curve
            crest_path = QPainterPath()
            crest_path.moveTo(0, mid_y)
            for x in range(0, w + step, step):
                envelope = math.sin((x / w) * math.pi)
                y_disp = (
                    math.sin(x * freq + phase_offset) * 0.75
                    + math.sin(x * freq * 1.6 - phase_offset * 0.6) * 0.25
                ) * amp * envelope
                crest_path.lineTo(x, mid_y + y_disp)
            painter.drawPath(crest_path)
