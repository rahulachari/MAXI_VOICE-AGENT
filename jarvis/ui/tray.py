"""
JARVIS System Tray Interface
Manages background system tray icon, context menu, and quick action signals.
"""

from PySide6.QtCore import Signal, QObject
from PySide6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor
from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from jarvis.app.config import config


def create_tray_icon() -> QIcon:
    """Generates a high-DPI glowing cyan/blue VoiceOS orb icon dynamically."""
    pix = QPixmap(64, 64)
    pix.fill(QColor(0, 0, 0, 0))

    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)

    # Outer glow
    painter.setPen(QColor(0, 240, 255, 120))
    painter.setBrush(QColor(10, 16, 30, 240))
    painter.drawEllipse(6, 6, 52, 52)

    # Core arc-reactor ring
    painter.setPen(QColor(0, 240, 255, 255))
    painter.setBrush(QColor(0, 229, 255, 200))
    painter.drawEllipse(18, 18, 28, 28)

    painter.setBrush(QColor(255, 255, 255, 255))
    painter.drawEllipse(26, 26, 12, 12)

    painter.end()
    return QIcon(pix)


class SystemTray(QObject):
    activate_requested = Signal()
    history_requested = Signal()
    settings_requested = Signal()
    mode_toggled = Signal(str)
    restart_requested = Signal()
    exit_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tray = QSystemTrayIcon(create_tray_icon(), parent)
        self.tray.setToolTip("JARVIS VoiceOS (Press Ctrl+Alt or click)")

        self._menu = QMenu()
        self._build_menu()
        self.tray.setContextMenu(self._menu)
        self.tray.activated.connect(self._on_tray_activated)

    def show(self):
        self.tray.show()

    def hide(self):
        self.tray.hide()

    def _build_menu(self):
        # Header
        header = self._menu.addAction("JARVIS VoiceOS")
        header.setEnabled(False)
        self._menu.addSeparator()

        # Quick Actions
        act_activate = self._menu.addAction("Activate (Ctrl+Alt)")
        act_activate.triggered.connect(self.activate_requested.emit)

        act_history = self._menu.addAction("History (Ctrl+Alt+H)")
        act_history.triggered.connect(self.history_requested.emit)

        self._menu.addSeparator()

        # Mode Toggles
        self.act_mode_agent = self._menu.addAction("Mode: Agent Mode")
        self.act_mode_agent.setCheckable(True)
        self.act_mode_agent.setChecked(config.get("active_mode", "agent") == "agent")
        self.act_mode_agent.triggered.connect(lambda: self._set_mode("agent"))

        self.act_mode_dict = self._menu.addAction("Mode: Dictation Mode")
        self.act_mode_dict.setCheckable(True)
        self.act_mode_dict.setChecked(config.get("active_mode", "agent") == "dictation")
        self.act_mode_dict.triggered.connect(lambda: self._set_mode("dictation"))

        self._menu.addSeparator()

        # Settings & Admin
        act_settings = self._menu.addAction("Settings...")
        act_settings.triggered.connect(self.settings_requested.emit)

        self._menu.addSeparator()

        act_restart = self._menu.addAction("Restart")
        act_restart.triggered.connect(self.restart_requested.emit)

        act_exit = self._menu.addAction("Exit")
        act_exit.triggered.connect(self.exit_requested.emit)

    def _set_mode(self, mode: str):
        config.set("active_mode", mode)
        self.act_mode_agent.setChecked(mode == "agent")
        self.act_mode_dict.setChecked(mode == "dictation")
        self.mode_toggled.emit(mode)

    def _on_tray_activated(self, reason):
        if reason in [QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick]:
            self.activate_requested.emit()
