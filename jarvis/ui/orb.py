"""
JARVIS VoiceOS Monochromatic Transparent Liquid Orb
Pure crystal-clarity liquid glass and monochrome metallic fluid ribbons.
Completely zero-color design: pure white, platinum, silver, cement, and translucent graphite glass.
Silky smooth GPU-accelerated 60 FPS rendering with zero WebEngine latency.
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

    def __init__(self, parent=None, size: int = 30):
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

        # ~60 FPS update loop
        self._timer = QTimer(self)
        self._timer.setInterval(16)
        self._timer.timeout.connect(self._on_tick)
        self._timer.start()

    def set_state(self, state: str):
        self._state = (state or "IDLE").upper()
        if self._state == "REST":
            self._target_energy = 0.0
            self._energy = 0.0
            if self._timer.isActive():
                self._timer.stop()
            self.update()
            return

        if not self._timer.isActive():
            self._timer.start()

        if self._state == "IDLE":
            self._target_energy = 0.08
        elif self._state in ["PROCESSING", "THINKING"]:
            self._target_energy = 0.60
        elif self._state in ["SPEAKING", "LISTENING"]:
            self._target_energy = 0.80
        self.update()

    def set_energy(self, energy: float):
        e = max(0.0, min(1.0, energy))
        boosted = math.pow(e, 0.55) * 1.3
        self._target_energy = max(0.08, min(1.0, boosted))

    def _on_tick(self):
        self._energy += (self._target_energy - self._energy) * 0.16

        is_active = self._state in ["PROCESSING", "THINKING", "SPEAKING", "LISTENING"]
        speed = (1.10 + self._energy * 0.8) if is_active else 0.35

        self._phase += 0.035 * speed
        self._rotation += 0.02 * speed
        self._pulse = math.sin(self._phase * 1.8) * 0.5 + 0.5
        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def paintEvent(self, event):
        if self._state == "REST":
            return
        w = self.width()
        h = self.height()
        if w <= 0 or h <= 0:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        cx = w / 2.0
        cy = h / 2.0
        base_radius = min(w, h) * 0.43

        is_active = self._state in ["PROCESSING", "THINKING", "SPEAKING", "LISTENING"]

        # -------------------------------------------------------------
        # 1. Subtle Translucent White Ambient Aura (Zero Colors)
        # -------------------------------------------------------------
        glow_rad = base_radius * (1.25 + self._energy * 0.30)
        glow_grad = QRadialGradient(cx, cy, glow_rad)
        glow_alpha = int(35 + self._energy * 45) if is_active else 20
        glow_grad.setColorAt(0.0, QColor(255, 255, 255, glow_alpha))
        glow_grad.setColorAt(0.60, QColor(226, 232, 240, int(glow_alpha * 0.40)))
        glow_grad.setColorAt(1.0, QColor(0, 0, 0, 0))

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(glow_grad))
        painter.drawEllipse(QPointF(cx, cy), glow_rad, glow_rad)

        # -------------------------------------------------------------
        # 2. Pure Transparent Liquid Glass Base (Zero Colors)
        # -------------------------------------------------------------
        current_rad = base_radius * (0.97 + self._energy * 0.05)
        clip_path = QPainterPath()
        clip_path.addEllipse(QPointF(cx, cy), current_rad, current_rad)

        painter.save()
        painter.setClipPath(clip_path)

        # High-transparency dark glass body
        base_grad = QRadialGradient(cx - current_rad * 0.25, cy - current_rad * 0.25, current_rad * 1.35)
        base_grad.setColorAt(0.0, QColor(25, 28, 35, 160))
        base_grad.setColorAt(0.60, QColor(10, 12, 16, 200))
        base_grad.setColorAt(1.0, QColor(3, 4, 6, 240))
        painter.setBrush(QBrush(base_grad))
        painter.drawEllipse(QPointF(cx, cy), current_rad, current_rad)

        # -------------------------------------------------------------
        # 3. Monochromatic Liquid Metal Fluid Ribbons (Silver, Platinum, White)
        #    Rotated at metalAngle (65° = 1.134 rad) — Absolutely NO colors!
        # -------------------------------------------------------------
        angle_rad = 1.134
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        evolution = (1.0 + self._energy * 0.5) if is_active else 0.40

        # Pure monochrome silver/platinum/graphite ribbons
        ribbons = [
            # Background soft platinum ribbon
            {
                "color": QColor(203, 213, 225),  # Cement Silver
                "alpha": int(100 + self._energy * 90) if is_active else 65,
                "amp_mult": 0.28,
                "freq": 2.1,
                "offset": 0.0,
                "stroke_w": 0.13,
            },
            # Primary luminous white ribbon
            {
                "color": QColor(255, 255, 255),  # Pure White
                "alpha": int(145 + self._energy * 95) if is_active else 100,
                "amp_mult": 0.32,
                "freq": 2.4,
                "offset": 1.4,
                "stroke_w": 0.11,
            },
            # Translucent graphite depth fold
            {
                "color": QColor(148, 163, 184),  # Slate / Graphite
                "alpha": int(80 + self._energy * 75) if is_active else 50,
                "amp_mult": 0.26,
                "freq": 2.7,
                "offset": 2.8,
                "stroke_w": 0.12,
            },
            # Frosted silver harmonic ribbon
            {
                "color": QColor(226, 232, 240),  # Frosted Platinum
                "alpha": int(115 + self._energy * 85) if is_active else 75,
                "amp_mult": 0.22,
                "freq": 1.8,
                "offset": 4.1,
                "stroke_w": 0.10,
            },
        ]

        steps = 32
        for r in ribbons:
            color = r["color"]
            alpha = r["alpha"]
            amp = r["amp_mult"] * current_rad * (0.6 + self._energy * 0.6) * evolution
            freq = r["freq"]
            offset = r["offset"]
            stroke_mult = r["stroke_w"]

            path = QPainterPath()
            first = True
            for i in range(steps + 1):
                t = i / steps
                rx = -current_rad + t * (2.0 * current_rad)
                rel_x = rx / current_rad
                envelope = max(0.0, 1.0 - rel_x * rel_x)

                wave = math.sin(t * math.pi * freq + self._phase * 1.2 + offset) * amp * envelope
                wave += math.sin(rel_x * 4.0 - self._phase * 0.8 + offset * 0.5) * (amp * 0.22) * envelope

                px = cx + rx * cos_a - wave * sin_a
                py = cy + rx * sin_a + wave * cos_a

                if first:
                    path.moveTo(px, py)
                    first = False
                else:
                    path.lineTo(px, py)

            pen = QPen(QColor(color.red(), color.green(), color.blue(), alpha), max(1.4, current_rad * stroke_mult))
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(path)

        # -------------------------------------------------------------
        # 4. White Core Crest Filament (High-Clarity Centerline)
        # -------------------------------------------------------------
        core_amp = current_rad * 0.20 * (0.65 + self._energy * 0.75)
        core_path = QPainterPath()
        first = True
        for i in range(steps + 1):
            t = i / steps
            rx = -current_rad + t * (2.0 * current_rad)
            rel_x = rx / current_rad
            envelope = max(0.0, 1.0 - rel_x * rel_x)
            wave = math.sin(t * math.pi * 2.3 + self._phase * 1.4) * core_amp * envelope

            px = cx + rx * cos_a - wave * sin_a
            py = cy + rx * sin_a + wave * cos_a

            if first:
                core_path.moveTo(px, py)
                first = False
            else:
                core_path.lineTo(px, py)

        core_alpha = int(210 + self._energy * 45) if is_active else 140
        core_pen = QPen(QColor(255, 255, 255, core_alpha), max(1.0, current_rad * 0.055))
        core_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(core_pen)
        painter.drawPath(core_path)

        # -------------------------------------------------------------
        # 5. Monochromatic Glass Specular Highlights (Zero Color)
        # -------------------------------------------------------------
        # Top-left key highlight (pure white/silver)
        key_x = cx - current_rad * 0.32
        key_y = cy - current_rad * 0.32
        key_rad = current_rad * 0.50
        key_grad = QRadialGradient(key_x, key_y, key_rad)
        key_grad.setColorAt(0.0, QColor(255, 255, 255, int(80 + self._energy * 60)))
        key_grad.setColorAt(0.5, QColor(241, 245, 249, int(35 + self._energy * 25)))
        key_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(key_grad))
        painter.drawEllipse(QPointF(key_x, key_y), key_rad, key_rad)

        painter.restore()

        # -------------------------------------------------------------
        # 6. Crystal-Clear Liquid Glass Hairline Specular Rim & Glint
        # -------------------------------------------------------------
        rim_pen = QPen(QColor(255, 255, 255, 110), 1.0)
        painter.setPen(rim_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), current_rad, current_rad)

        # Crisp top-left lens glint
        glint_rx = current_rad * 0.36
        glint_ry = current_rad * 0.17
        gx = cx - current_rad * 0.28
        gy = cy - current_rad * 0.38

        glint_grad = QLinearGradient(gx, gy, gx, gy + glint_ry * 2.0)
        glint_grad.setColorAt(0.0, QColor(255, 255, 255, 230))
        glint_grad.setColorAt(0.5, QColor(255, 255, 255, 80))
        glint_grad.setColorAt(1.0, QColor(255, 255, 255, 0))

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(glint_grad))
        painter.drawEllipse(QPointF(gx, gy + glint_ry), glint_rx, glint_ry)
