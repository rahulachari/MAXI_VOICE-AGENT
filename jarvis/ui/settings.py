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
        self.combo_provider.addItems(["gemini", "groq", "openai", "local"])
        self.combo_provider.setCurrentText(config.get("ai_provider", "gemini"))
        l.addWidget(self.combo_provider)

        l.addWidget(QLabel("Google Gemini API Key:"))
        self.input_gemini_key = QLineEdit()
        self.input_gemini_key.setEchoMode(QLineEdit.Password)
        self.input_gemini_key.setText(config.get("gemini_api_key", ""))
        self.input_gemini_key.setPlaceholderText("AIzaSy...")
        l.addWidget(self.input_gemini_key)

        l.addWidget(QLabel("Default Home City / Weather Location:"))
        self.input_default_city = QLineEdit()
        self.input_default_city.setText(config.get("default_city", "Chittoor"))
        self.input_default_city.setPlaceholderText("e.g. Chittoor, Tirupati, Bangalore, Mumbai...")
        l.addWidget(self.input_default_city)

        l.addWidget(QLabel("Weather API Key (OpenWeatherMap, Optional):"))
        self.input_weather_key = QLineEdit()
        self.input_weather_key.setEchoMode(QLineEdit.Password)
        self.input_weather_key.setText(config.get("weather_api_key", ""))
        self.input_weather_key.setPlaceholderText("Optional: Leave empty for free global live satellite reports")
        l.addWidget(self.input_weather_key)

        l.addWidget(QLabel("Groq API Key (Ultra-Low-Latency Cloud Reasoning & STT):"))
        self.input_groq_key = QLineEdit()
        self.input_groq_key.setEchoMode(QLineEdit.Password)
        self.input_groq_key.setText(config.get("groq_api_key", ""))
        self.input_groq_key.setPlaceholderText("gsk_...")
        l.addWidget(self.input_groq_key)

        l.addStretch()
        return tab

    def _create_audio_tab(self) -> QWidget:
        tab = QWidget()
        l = QVBoxLayout(tab)
        l.setContentsMargins(16, 16, 16, 16)
        l.setSpacing(12)

        l.addWidget(QLabel("AI Voice (Humanized Studio Voice):"))
        self.combo_voice = QComboBox()
        voices = [
            ("Lyra (Gemini Lady Voice - Humanized Studio)", "lyra"),
            ("Jenny (US Warm Natural Female)", "en-US-JennyNeural"),
            ("Aria (US Professional Female)", "en-US-AriaNeural"),
            ("Sonia (UK Elegant Female)", "en-GB-SoniaNeural"),
            ("Ava (US Expressive Female)", "en-US-AvaNeural"),
            ("Brian (UK Articulate Male)", "en-US-BrianNeural"),
        ]
        curr_v = str(config.get("voice_name", "lyra")).lower()
        for idx, (label, val) in enumerate(voices):
            self.combo_voice.addItem(label, val)
            if val.lower() == curr_v or (val == "lyra" and "lyra" in curr_v):
                self.combo_voice.setCurrentIndex(idx)
        l.addWidget(self.combo_voice)

        l.addWidget(QLabel("Speech-To-Text Provider:"))
        self.combo_stt = QComboBox()
        self.combo_stt.addItems(["google", "groq_whisper"])
        self.combo_stt.setCurrentText(config.get("stt_provider", "google"))
        l.addWidget(self.combo_stt)

        l.addWidget(QLabel("Speech Rate (Words per minute):"))
        self.slider_rate = QSlider(Qt.Horizontal)
        self.slider_rate.setRange(120, 240)
        self.slider_rate.setValue(config.get("tts_rate", 190))
        l.addWidget(self.slider_rate)

        # Test Voice Button
        btn_test_tts = QPushButton("Test Voice Output")
        def _test_speech():
            chosen = self.combo_voice.currentData() or "lyra"
            tts_engine._voice = chosen
            tts_engine.speak("Hello Rahul, I am your personal AI assistant. How may I assist you?")
        btn_test_tts.clicked.connect(_test_speech)
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
        config.set("default_city", self.input_default_city.text().strip(), auto_save=False)
        config.set("gemini_api_key", self.input_gemini_key.text().strip(), auto_save=False)
        config.set("weather_api_key", self.input_weather_key.text().strip(), auto_save=False)
        config.set("groq_api_key", self.input_groq_key.text(), auto_save=False)
        config.set("stt_provider", self.combo_stt.currentText(), auto_save=False)
        config.set("tts_rate", self.slider_rate.value(), auto_save=False)
        config.set("activation_hotkey", self.input_hotkey_act.text(), auto_save=False)
        config.set("history_hotkey", self.input_hotkey_hist.text(), auto_save=False)
        config.set("save_history", self.chk_save_history.isChecked(), auto_save=False)
        config.set("confirm_destructive", self.chk_confirm.isChecked(), auto_save=True)

        self.settings_saved.emit()
        self.accept()
