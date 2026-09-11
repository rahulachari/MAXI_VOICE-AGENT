"""
JARVIS Settings Dialog
Futuristic tabbed settings interface for audio, AI providers, shortcuts, and privacy.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QWidget,
    QLabel,
    QLineEdit,
    QComboBox,
    QSlider,
    QCheckBox,
    QPushButton,
    QMessageBox,
)
import sounddevice as sd
from jarvis.app.config import config
from jarvis.storage.database import get_db_path
from jarvis.voice.text_to_speech import tts_engine


class SettingsDialog(QDialog):
    settings_saved = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("JARVIS VoiceOS Settings")
        self.setFixedSize(520, 460)
        self.setStyleSheet("""
            QDialog {
                background-color: #0d1322;
                color: #f8fafc;
            }
            QTabWidget::pane {
                border: 1px solid rgba(0, 240, 255, 0.25);
                background: #111a2e;
                border-radius: 8px;
            }
            QTabBar::tab {
                background: #090e1a;
                color: #94a3b8;
                padding: 8px 16px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: 500;
            }
            QTabBar::tab:selected {
                color: #00f0ff;
                background: #111a2e;
                border-bottom: 2px solid #00f0ff;
            }
            QLabel {
                color: #cbd5e1;
                font-size: 12px;
            }
            QLineEdit, QComboBox {
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(0, 240, 255, 0.2);
                border-radius: 6px;
                color: white;
                padding: 6px 10px;
                font-size: 12px;
            }
            QPushButton {
                background: rgba(0, 240, 255, 0.15);
                color: #00f0ff;
                border: 1px solid rgba(0, 240, 255, 0.3);
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: rgba(0, 240, 255, 0.25);
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_ai_tab(), "AI Engine")
        self.tabs.addTab(self._create_audio_tab(), "Voice & Audio")
        self.tabs.addTab(self._create_shortcuts_tab(), "Hotkeys")
        self.tabs.addTab(self._create_privacy_tab(), "Privacy & History")

        layout.addWidget(self.tabs)

        # Bottom buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Save Settings")
        btn_save.setStyleSheet("background: #00b4d8; color: white; border: none;")
        btn_save.clicked.connect(self._save_settings)

        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def _create_ai_tab(self) -> QWidget:
        tab = QWidget()
        l = QVBoxLayout(tab)
        l.setContentsMargins(16, 16, 16, 16)
        l.setSpacing(12)

        l.addWidget(QLabel("Primary AI Provider:"))
        self.combo_provider = QComboBox()
        self.combo_provider.addItems(["groq", "openai", "gemini", "local"])
        self.combo_provider.setCurrentText(config.get("ai_provider", "groq"))
        l.addWidget(self.combo_provider)

        l.addWidget(QLabel("AI Model Name:"))
        self.input_model = QLineEdit()
        self.input_model.setText(config.get("ai_model", "openai/gpt-oss-120b"))
        l.addWidget(self.input_model)

        l.addWidget(QLabel("Groq API Key:"))
        self.input_groq_key = QLineEdit()
        self.input_groq_key.setEchoMode(QLineEdit.Password)
        self.input_groq_key.setText(config.get("groq_api_key", ""))
        l.addWidget(self.input_groq_key)

        l.addStretch()
        return tab

    def _create_audio_tab(self) -> QWidget:
        tab = QWidget()
        l = QVBoxLayout(tab)
        l.setContentsMargins(16, 16, 16, 16)
        l.setSpacing(12)

        l.addWidget(QLabel("Speech-To-Text Provider:"))
        self.combo_stt = QComboBox()
        self.combo_stt.addItems(["groq_whisper", "google"])
        self.combo_stt.setCurrentText(config.get("stt_provider", "groq_whisper"))
        l.addWidget(self.combo_stt)

        l.addWidget(QLabel("Speech Rate (Words per minute):"))
        self.slider_rate = QSlider(Qt.Horizontal)
        self.slider_rate.setRange(120, 240)
        self.slider_rate.setValue(config.get("tts_rate", 185))
        l.addWidget(self.slider_rate)

        # Test Voice Button
        btn_test_tts = QPushButton("Test Voice Synthesis")
        btn_test_tts.clicked.connect(lambda: tts_engine.speak("JARVIS voice synthesis operational."))
        l.addWidget(btn_test_tts)

        l.addStretch()
        return tab

    def _create_shortcuts_tab(self) -> QWidget:
        tab = QWidget()
        l = QVBoxLayout(tab)
        l.setContentsMargins(16, 16, 16, 16)
        l.setSpacing(12)

        l.addWidget(QLabel("Global Activation Hotkey:"))
        self.input_hotkey_act = QLineEdit()
        self.input_hotkey_act.setText(config.get("activation_hotkey", "ctrl+alt"))
        l.addWidget(self.input_hotkey_act)

        l.addWidget(QLabel("History Sidebar Hotkey:"))
        self.input_hotkey_hist = QLineEdit()
        self.input_hotkey_hist.setText(config.get("history_hotkey", "ctrl+alt+h"))
        l.addWidget(self.input_hotkey_hist)

        l.addWidget(QLabel("Note: Global hotkeys operate from any active Windows application."))

        l.addStretch()
        return tab

    def _create_privacy_tab(self) -> QWidget:
        tab = QWidget()
        l = QVBoxLayout(tab)
        l.setContentsMargins(16, 16, 16, 16)
        l.setSpacing(12)

        self.chk_save_history = QCheckBox("Save voice command history locally")
        self.chk_save_history.setChecked(config.get("save_history", True))
        l.addWidget(self.chk_save_history)

        self.chk_confirm = QCheckBox("Require confirmation for destructive operations")
        self.chk_confirm.setChecked(config.get("confirm_destructive", True))
        l.addWidget(self.chk_confirm)

        l.addWidget(QLabel(f"Database Location: {get_db_path()}"))

        btn_clear = QPushButton("Purge Today's History")
        btn_clear.setStyleSheet("color: #ff1744; border-color: rgba(255, 23, 68, 0.4);")
        btn_clear.clicked.connect(self._clear_history)
        l.addWidget(btn_clear)

        l.addStretch()
        return tab

    def _clear_history(self):
        from jarvis.storage.history_repository import HistoryRepository
        count = HistoryRepository().clear_today()
        QMessageBox.information(self, "History Purged", f"Cleared {count} items from today's history.")

    def _save_settings(self):
        config.set("ai_provider", self.combo_provider.currentText(), auto_save=False)
        config.set("ai_model", self.input_model.text(), auto_save=False)
        config.set("groq_api_key", self.input_groq_key.text(), auto_save=False)
        config.set("stt_provider", self.combo_stt.currentText(), auto_save=False)
        config.set("tts_rate", self.slider_rate.value(), auto_save=False)
        config.set("activation_hotkey", self.input_hotkey_act.text(), auto_save=False)
        config.set("history_hotkey", self.input_hotkey_hist.text(), auto_save=False)
        config.set("save_history", self.chk_save_history.isChecked(), auto_save=False)
        config.set("confirm_destructive", self.chk_confirm.isChecked(), auto_save=True)

        self.settings_saved.emit()
        self.accept()
