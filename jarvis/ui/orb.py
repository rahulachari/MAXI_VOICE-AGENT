"""
JARVIS VoiceOS Living Liquid Siri & Gemini Live Orb
Ultra-premium native 60 FPS procedural fluid bubbling orb with real-time
refraction, iridescent chromatic dispersion, and voice audio reactivity.
Zero WebEngine dependencies, 0ms startup, silky smooth GPU-rendered graphics.
"""

import math
import time
from PySide6.QtCore import Qt, Signal, QTimer, QPointF
from PySide6.QtGui import (
    QPainter,
    QPainterPath,
    QColor,
    QRadialGradient,
    QLinearGradient,
    QBrush,
    QPen,
    QMouseEvent,
)
from PySide6.QtWidgets import QWidget


class VoiceOSOrb(QWidget):
    clicked = Signal()

    def __init__(self, parent=None, size: int = 56):
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._state = "IDLE"
        self._energy = 0.05
        self._target_energy = 0.05
        self._phase = 0.0
        self._rotation = 0.0
        self._pulse = 0.0

        # High-FPS update loop
        self._timer = QTimer(self)
        self._timer.setInterval(16)  # ~60 FPS
        self._timer.timeout.connect(self._on_tick)
        self._timer.start()

    def set_state(self, state: str):
        self._state = (state or "IDLE").upper()
        if self._state == "IDLE":
            self._target_energy = 0.08
        elif self._state in ["PROCESSING", "THINKING"]:
            self._target_energy = 0.55
        elif self._state in ["SPEAKING"]:
            self._target_energy = 0.70
        self.update()

    def set_energy(self, energy: float):
        e = max(0.0, min(1.0, energy))
        boosted = math.pow(e, 0.55) * 1.3
        self._target_energy = max(0.08, min(1.0, boosted))

    def _on_tick(self):
        # Smooth energy interpolation
        self._energy += (self._target_energy - self._energy) * 0.16

        # Speed modulation based on state & energy
        if self._state in ["PROCESSING", "THINKING"]:
            speed = 2.4
        elif self._state == "SPEAKING":
            speed = 1.8
        elif self._state == "LISTENING":
            speed = 1.2 + self._energy * 2.0
        else:
            speed = 0.6

        self._phase += 0.03 * speed
        self._rotation += 0.02 * speed
        self._pulse = math.sin(self._phase * 1.8) * 0.5 + 0.5
        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def paintEvent(self, event):
        w = self.width()
        h = self.height()
        if w <= 0 or h <= 0:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        cx = w / 2.0
        cy = h / 2.0
        base_radius = min(w, h) * 0.40

        # State color palettes (Siri & Gemini Live hues)
        if self._state in ["LISTENING"]:
            c_core = QColor(0, 242, 254)       # Bright Electric Cyan
            c_mid = QColor(79, 172, 254)       # Deep Aqua
            c_outer = QColor(0, 114, 255)      # Sapphire
            c_rim = QColor(0, 255, 230, 200)   # Neon Teal
        elif self._state in ["PROCESSING", "THINKING"]:
            c_core = QColor(0, 242, 254)       # Cyan
            c_mid = QColor(178, 36, 239)       # Violet
            c_outer = QColor(240, 147, 251)    # Magenta
            c_rim = QColor(255, 255, 255, 220) # Bright White
        elif self._state in ["SPEAKING"]:
            c_core = QColor(117, 121, 255)     # Lavender Blue
            c_mid = QColor(178, 36, 239)       # Royal Violet
            c_outer = QColor(0, 198, 255)      # Cyan Blue
            c_rim = QColor(240, 147, 251, 210) # Iridescent Pink
        elif self._state in ["ERROR"]:
            c_core = QColor(255, 75, 43)       # Flame Red
            c_mid = QColor(255, 65, 108)       # Crimson
            c_outer = QColor(180, 20, 50)      # Deep Blood
            c_rim = QColor(255, 120, 120, 200)
        else:  # IDLE
            c_core = QColor(0, 180, 255)       # Calm Neon Sky
            c_mid = QColor(10, 80, 200)        # Deep Sapphire
            c_outer = QColor(5, 25, 80)        # OLED Abyss
            c_rim = QColor(0, 200, 255, 120)

        # 1. Radiant Ambient Glow (surges with energy)
        glow_rad = base_radius * (1.25 + self._energy * 0.45)
        glow_grad = QRadialGradient(cx, cy, glow_rad)
        glow_c = QColor(c_core)
        glow_c.setAlpha(int(60 + self._energy * 100))
        glow_grad.setColorAt(0.0, glow_c)
        glow_grad.setColorAt(0.65, QColor(c_mid.red(), c_mid.green(), c_mid.blue(), int(30 + self._energy * 40)))
        glow_grad.setColorAt(1.0, QColor(0, 0, 0, 0))

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(glow_grad))
        painter.drawEllipse(QPointF(cx, cy), glow_rad, glow_rad)

        # 2. Fluid Bubbling Lobes (3 organic undulating harmonic lobes)
        num_points = 48
        current_rad = base_radius * (0.92 + self._energy * 0.22)
        path = QPainterPath()

        for i in range(num_points):
            theta = (i / float(num_points)) * 2 * math.pi
            # Bubbling deformation formula: 3-lobe + 2-lobe interference
            wave1 = math.sin(theta * 3.0 + self._phase * 2.1) * (0.07 + self._energy * 0.12)
            wave2 = math.cos(theta * 2.0 - self._phase * 1.7) * (0.05 + self._energy * 0.08)
            wave3 = math.sin(theta * 5.0 + self._phase * 3.2) * (0.02 + self._energy * 0.05)

            r_i = current_rad * (1.0 + wave1 + wave2 + wave3)
            px = cx + r_i * math.cos(theta + self._rotation)
            py = cy + r_i * math.sin(theta + self._rotation)

            if i == 0:
                path.moveTo(px, py)
            else:
                path.lineTo(px, py)

        path.closeSubpath()

        # 3. Fluid Body Gradient (Living Plasma)
        core_grad = QRadialGradient(cx - current_rad * 0.25, cy - current_rad * 0.25, current_rad * 1.3)
        core_grad.setColorAt(0.0, c_core)
        core_grad.setColorAt(0.45, c_mid)
        core_grad.setColorAt(0.85, c_outer)
        core_grad.setColorAt(1.0, QColor(0, 0, 0, 180))

        painter.setBrush(QBrush(core_grad))
        painter.setPen(Qt.NoPen)
        painter.drawPath(path)

        # 4. Iridescent Glass Specular Rim Highlight (Apple Siri style)
        rim_pen = QPen(c_rim, max(1.2, current_rad * 0.08))
        painter.setPen(rim_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)

        # 5. Caustic Specular Glint (Top-left lens reflection)
        glint_w = current_rad * 0.45
        glint_h = current_rad * 0.22
        glint_x = cx - current_rad * 0.50
        glint_y = cy - current_rad * 0.55

        glint_grad = QLinearGradient(glint_x, glint_y, glint_x, glint_y + glint_h)
        glint_grad.setColorAt(0.0, QColor(255, 255, 255, 210))
        glint_grad.setColorAt(1.0, QColor(255, 255, 255, 0))

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(glint_grad))
        painter.drawEllipse(QPointF(glint_x + glint_w / 2.0, glint_y + glint_h / 2.0), glint_w / 2.0, glint_h / 2.0)
