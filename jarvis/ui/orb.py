"""
JARVIS VoiceOS Living Orb & Dynamic Waveform Widget
Clean, glossy pure-white and pearl visualizer with real-time 4-band audio waveform.
"""

from PySide6.QtCore import Qt, QTimer, QRectF
from PySide6.QtGui import QPainter, QColor, QRadialGradient, QBrush
from PySide6.QtWidgets import QWidget


class VoiceOSOrb(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(32, 32)
        self.setCursor(Qt.PointingHandCursor)

        self._state = "IDLE"  # IDLE, LISTENING, PROCESSING, EXECUTING, SPEAKING, CONFIRMATION, ERROR
        self._pulse_phase = 0.0
        self._rotation = 0.0
        self._energy = 0.0  # 0.0 to 1.0 from microphone
        self._bar_heights = [4.0, 6.0, 5.0, 4.0]

        # 60 FPS animation timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate_step)
        self.timer.start(16)

    def set_state(self, state: str):
        self._state = state
        self.update()

    def set_energy(self, energy: float):
        self._energy = max(0.0, min(1.0, energy))

    def _animate_step(self):
        self._pulse_phase = (self._pulse_phase + 0.06) % 6.28318
        self._rotation = (self._rotation + 1.5) % 360.0

        # Target heights for the 4 waveform bars
        if self._state == "LISTENING":
            e = self._energy
            self._bar_heights[0] += (max(4.0, e * 18.0) - self._bar_heights[0]) * 0.35
            self._bar_heights[1] += (max(6.0, e * 24.0) - self._bar_heights[1]) * 0.4
            self._bar_heights[2] += (max(5.0, e * 22.0) - self._bar_heights[2]) * 0.35
            self._bar_heights[3] += (max(4.0, e * 16.0) - self._bar_heights[3]) * 0.3
        elif self._state == "SPEAKING":
            import math
            self._bar_heights[0] = 5.0 + 4.0 * math.sin(self._pulse_phase)
            self._bar_heights[1] = 7.0 + 6.0 * math.sin(self._pulse_phase + 0.8)
            self._bar_heights[2] = 6.0 + 5.0 * math.sin(self._pulse_phase + 1.6)
            self._bar_heights[3] = 4.0 + 3.0 * math.sin(self._pulse_phase + 2.4)
        else:
            for i in range(4):
                self._bar_heights[i] += (4.0 - self._bar_heights[i]) * 0.2

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        import math
        w = self.width()
        h = self.height()
        cx = w / 2.0
        cy = h / 2.0
        r = 12.0  # Globe radius

        # 1. Soft atmospheric outer glow
        glow_r = r * 1.55
        grad_glow = QRadialGradient(cx, cy, glow_r)
        if self._state == "ERROR":
            glow_color = QColor(255, 60, 60, 100)
        elif self._state == "CONFIRMATION_REQUIRED":
            glow_color = QColor(255, 180, 50, 100)
        elif self._state == "EXECUTING":
            glow_color = QColor(50, 255, 160, 110)
        else:
            glow_color = QColor(0, 200, 255, 120)

        grad_glow.setColorAt(0.0, glow_color)
        grad_glow.setColorAt(0.6, QColor(glow_color.red(), glow_color.green(), glow_color.blue(), 30))
        grad_glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(grad_glow))
        painter.drawEllipse(QRectF(cx - glow_r, cy - glow_r, glow_r * 2, glow_r * 2))

        # 2. Celestial globe body (VoiceOS Earth sphere)
        sphere_grad = QRadialGradient(cx - r * 0.35, cy - r * 0.35, r * 1.3)
        if self._state == "ERROR":
            sphere_grad.setColorAt(0.0, QColor(255, 100, 100))
            sphere_grad.setColorAt(0.7, QColor(180, 20, 20))
            sphere_grad.setColorAt(1.0, QColor(60, 10, 10))
        else:
            sphere_grad.setColorAt(0.0, QColor(0, 235, 255))
            sphere_grad.setColorAt(0.4, QColor(0, 120, 240))
            sphere_grad.setColorAt(0.85, QColor(8, 28, 75))
            sphere_grad.setColorAt(1.0, QColor(3, 8, 25))

        painter.setBrush(QBrush(sphere_grad))
        painter.drawEllipse(QRectF(cx - r, cy - r, r * 2, r * 2))

        # 3. Delicate orbital / longitude curve arcs
        painter.setPen(QColor(255, 255, 255, 60))
        painter.drawEllipse(QRectF(cx - r * 0.55, cy - r, r * 1.1, r * 2))
        painter.drawEllipse(QRectF(cx - r, cy - r * 0.45, r * 2, r * 0.9))

        # 4. In Listening or Speaking mode: 4-band audio waveform in center
        if self._state in ["LISTENING", "SPEAKING"]:
            bar_w = 2.5
            gap = 2.5
            total_bw = 4 * bar_w + 3 * gap
            start_x = cx - total_bw / 2.0

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(255, 255, 255, 255)))

            for i in range(4):
                bh = min(r * 1.6, self._bar_heights[i])
                bx = start_x + i * (bar_w + gap)
                by = cy - (bh / 2.0)
                painter.drawRoundedRect(QRectF(bx, by, bar_w, bh), 1.2, 1.2)
        else:
            # Idle gentle breathing inner core
            core_pulse = 1.0 + 0.15 * math.sin(self._pulse_phase)
            core_r = 3.5 * core_pulse
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(255, 255, 255, 230)))
            painter.drawEllipse(QRectF(cx - core_r, cy - core_r, core_r * 2, core_r * 2))

        # 5. Apple Liquid Glass Specular Caustic Highlight (top-left glass lens reflection)
        caustic_grad = QRadialGradient(cx - r * 0.4, cy - r * 0.45, r * 0.8)
        caustic_grad.setColorAt(0.0, QColor(255, 255, 255, 180))
        caustic_grad.setColorAt(0.4, QColor(255, 255, 255, 60))
        caustic_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(caustic_grad))
        painter.drawEllipse(QRectF(cx - r * 0.75, cy - r * 0.85, r * 1.2, r * 0.8))

        # 6. Ultra-thin glass perimeter rim
        painter.setPen(QColor(255, 255, 255, 75))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QRectF(cx - r, cy - r, r * 2, r * 2))
