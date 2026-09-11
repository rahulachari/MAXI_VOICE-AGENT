"""
JARVIS System Tray Interface
Manages background system tray icon, context menu, Pause/Resume controls,
and native Windows Launch-at-Startup persistence in the Windows Registry.
"""

import os
import sys
from PySide6.QtCore import Signal, QObject
from PySide6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor
from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from jarvis.app.config import config


def is_launch_at_startup() -> bool:
    """Checks Windows Registry to see if JARVIS is registered in Run key."""
    if sys.platform != "win32":
        return False
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_READ,
        )
        val, _ = winreg.QueryValueEx(key, "JARVIS_VoiceOS")
        winreg.CloseKey(key)
        return bool(val)
    except Exception:
        return False


def set_launch_at_startup(enable: bool) -> bool:
    """Registers or unregisters JARVIS in the Windows Registry Run key."""
    if sys.platform != "win32":
        return False
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE,
        )
        if enable:
            if getattr(sys, "frozen", False):
                exe_path = sys.executable
                cmd = f'"{exe_path}"'
            else:
                script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "run.py"))
                cmd = f'"{sys.executable}" "{script_path}"'
            winreg.SetValueEx(key, "JARVIS_VoiceOS", 0, winreg.REG_SZ, cmd)
        else:
            try:
                winreg.DeleteValue(key, "JARVIS_VoiceOS")
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
        return True
    except Exception as e:
        print(f"[Tray] Registry startup configuration error: {e}")
        return False


def create_tray_icon(paused: bool = False) -> QIcon:
    """Generates a high-DPI glowing VoiceOS orb icon dynamically."""
    pix = QPixmap(64, 64)
    pix.fill(QColor(0, 0, 0, 0))

    painter = QPainter(pix)
    painter.setRenderHint(QPainter.Antialiasing)

    if paused:
        # Amber/Muted ring for paused state
        painter.setPen(QColor(245, 158, 11, 140))
        painter.setBrush(QColor(24, 20, 16, 240))
        painter.drawEllipse(6, 6, 52, 52)

        painter.setPen(QColor(245, 158, 11, 255))
        painter.setBrush(QColor(245, 158, 11, 200))
        painter.drawRect(22, 20, 6, 24)
        painter.drawRect(36, 20, 6, 24)
    else:
        # Glowing cyan VoiceOS arc-reactor
        painter.setPen(QColor(0, 240, 255, 120))
        painter.setBrush(QColor(10, 16, 30, 240))
        painter.drawEllipse(6, 6, 52, 52)

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
    pause_toggled = Signal(bool)
    mode_toggled = Signal(str)
    restart_requested = Signal()
    exit_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_paused = False
        self.tray = QSystemTrayIcon(create_tray_icon(paused=False), parent)
        self.tray.setToolTip("JARVIS VoiceOS (Active • Hold Ctrl+Alt to speak)")

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
        header = self._menu.addAction("⚡ JARVIS VoiceOS")
        header.setEnabled(False)
        self._menu.addSeparator()

        # Primary Quick Actions
        act_activate = self._menu.addAction("Activate (Ctrl+Alt)")
        act_activate.triggered.connect(self.activate_requested.emit)

        act_history = self._menu.addAction("History (Ctrl+Alt+H)")
        act_history.triggered.connect(self.history_requested.emit)

        self._menu.addSeparator()

        # Pause / Resume Control
        self.act_pause = self._menu.addAction("Pause Assistant")
        self.act_pause.triggered.connect(self._toggle_pause)

        # Launch at Login Control (Native Windows Registry Run Key)
        self.act_startup = self._menu.addAction("Launch at Startup")
        self.act_startup.setCheckable(True)
        self.act_startup.setChecked(is_launch_at_startup())
        self.act_startup.triggered.connect(self._toggle_startup)

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

        act_exit = self._menu.addAction("Quit JARVIS")
        act_exit.triggered.connect(self.exit_requested.emit)

    def _toggle_pause(self):
        self._is_paused = not self._is_paused
        if self._is_paused:
            self.act_pause.setText("Resume Assistant")
            self.tray.setIcon(create_tray_icon(paused=True))
            self.tray.setToolTip("JARVIS VoiceOS (Paused)")
        else:
            self.act_pause.setText("Pause Assistant")
            self.tray.setIcon(create_tray_icon(paused=False))
            self.tray.setToolTip("JARVIS VoiceOS (Active • Hold Ctrl+Alt to speak)")

        self.pause_toggled.emit(self._is_paused)

    def _toggle_startup(self, checked: bool):
        success = set_launch_at_startup(checked)
        self.act_startup.setChecked(is_launch_at_startup() if not success else checked)

    def _set_mode(self, mode: str):
        config.set("active_mode", mode)
        self.act_mode_agent.setChecked(mode == "agent")
        self.act_mode_dict.setChecked(mode == "dictation")
        self.mode_toggled.emit(mode)

    def _on_tray_activated(self, reason):
        if reason in [QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick]:
            self.activate_requested.emit()
