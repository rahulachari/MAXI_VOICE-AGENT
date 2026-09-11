"""
JARVIS VoiceOS Living Liquid Glass Orb
State-of-the-art Neural Plasma liquid glass orb with real-time refraction,
spectral dispersion, specular caustic highlights, and reactive energy pulse.
"""

import os
from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QPainter, QColor, QRadialGradient, QBrush
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtWebEngineWidgets import QWebEngineView


class VoiceOSOrb(QWidget):
    clicked = Signal()

    def __init__(self, parent=None, size: int = 56):
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)
        self.setCursor(Qt.PointingHandCursor)

        self._state = "IDLE"
        self._energy = 0.0
        self._is_loaded = False
        self._pending_state = "idle"

        # WebEngine setup for rendering the Neural Plasma liquid orb shader
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.web_view = QWebEngineView(self)
        self.web_view.setFixedSize(size, size)
        self.web_view.setStyleSheet("background: transparent; border: none;")
        self.web_view.page().setBackgroundColor(Qt.transparent)
        self.web_view.setContextMenuPolicy(Qt.NoContextMenu)
        layout.addWidget(self.web_view)

        # Asset location
        assets_dir = os.path.join(os.path.dirname(__file__), "assets")
        html_file = os.path.join(assets_dir, "liquid_orb.html")
        
        self.web_view.loadFinished.connect(self._on_load_finished)
        if os.path.exists(html_file):
            self.web_view.load(QUrl.fromLocalFile(os.path.abspath(html_file)))

    def _on_load_finished(self, ok: bool):
        self._is_loaded = bool(ok)
        if self._is_loaded:
            self.web_view.page().runJavaScript(
                f"window.liquidOrb && window.liquidOrb.setState('{self._pending_state}');"
            )

    def set_state(self, state: str):
        self._state = state
        st = state.lower()
        if st in ["processing", "analyzing", "thinking", "loading"]:
            mapped_state = "thinking"
        elif st in ["listening", "listening..."]:
            mapped_state = "listening"
        elif st in ["speaking", "talking"]:
            mapped_state = "speaking"
        elif st in ["error", "failed"]:
            mapped_state = "error"
        else:
            mapped_state = "idle"

        self._pending_state = mapped_state
        if self._is_loaded:
            self.web_view.page().runJavaScript(
                f"window.liquidOrb && window.liquidOrb.setState('{mapped_state}');"
            )
        self.update()

    def set_energy(self, energy: float):
        self._energy = max(0.0, min(1.0, energy))
        if self._is_loaded:
            self.web_view.page().runJavaScript(
                f"window.liquidOrb && window.liquidOrb.setEnergy({self._energy:.3f});"
            )

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def paintEvent(self, event):
        # Fallback gentle glow while WebEngine is loading
        if not self._is_loaded:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            w = self.width()
            h = self.height()
            cx = w / 2.0
            cy = h / 2.0
            r = min(w, h) * 0.42

            grad = QRadialGradient(cx, cy, r * 1.3)
            grad.setColorAt(0.0, QColor(0, 180, 255, 230))
            grad.setColorAt(0.6, QColor(0, 90, 220, 180))
            grad.setColorAt(1.0, QColor(5, 15, 50, 0))

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(grad))
            painter.drawEllipse(cx - r, cy - r, r * 2, r * 2)
            super().paintEvent(event)
