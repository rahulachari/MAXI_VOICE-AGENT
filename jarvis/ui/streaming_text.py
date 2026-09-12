"""
JARVIS VoiceOS Streaming Text Component
Words resolve smoothly with inline source citation chips, action icons
(Copy, Retry, Thumbs Up/Down, Sources toggle), collapsible citation accordion,
and clickable follow-up prompt suggestions.
"""

import os
from typing import List, Dict, Optional, Callable
from PySide6.QtCore import Qt, QTimer, Signal, QSize
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QApplication,
)
from PySide6.QtGui import QCursor, QFont, QIcon

_ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
_COPY_ICON = os.path.join(_ASSETS_DIR, "copy_icon.svg")
_CHECK_ICON = os.path.join(_ASSETS_DIR, "check_icon.svg")


DEFAULT_SOURCES = [
    {"name": "Web Knowledge", "domain": "search.google.com", "href": "https://google.com"},
    {"name": "Local System", "domain": "localhost", "href": "#"},
]

DEFAULT_FOLLOW_UPS = [
    "Tell me more details",
    "Run this in terminal",
]


class SourceChip(QPushButton):
    """Inline source chip with domain badge."""
    def __init__(self, domain: str = "source", parent=None):
        super().__init__(parent)
        self.setText(f"🌐 {domain}")
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.08);
                color: #94a3b8;
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 5px;
                padding: 1px 6px;
                font-size: 10.5px;
                font-family: 'Cascadia Code', 'Consolas', monospace;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.16);
                color: #f1f5f9;
                border-color: rgba(255, 255, 255, 0.25);
            }
        """)


class StreamingTextWidget(QWidget):
    follow_up_clicked = Signal(str)
    done_streaming = Signal()
    copy_requested = Signal(str)
    retry_requested = Signal()

    def __init__(
        self,
        text: str = "",
        sources: Optional[List[Dict[str, str]]] = None,
        follow_ups: Optional[List[str]] = None,
        word_ms: int = 45,
        parent=None,
    ):
        super().__init__(parent)
        self._full_text = text
        self._tokens = text.split() if text else []
        self._token_index = 0
        self._word_ms = word_ms
        self._sources = sources or []
        self._follow_ups = follow_ups or []
        self._sources_open = False

        self._init_ui()

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 4, 0, 4)
        self.main_layout.setSpacing(6)

        # 1. Streamed Body Text
        self.body_label = QLabel()
        self.body_label.setWordWrap(True)
        self.body_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.body_label.setStyleSheet("""
            color: #f1f5f9;
            font-size: 13.5px;
            line-height: 1.45;
            font-family: 'Segoe UI Variable Display', 'Segoe UI', -apple-system, sans-serif;
            background: transparent;
        """)
        self.main_layout.addWidget(self.body_label)

        # 2. Action Icons Row (Copy, Retry, Up, Down, Sources pill)
        self.actions_row = QWidget()
        act_layout = QHBoxLayout(self.actions_row)
        act_layout.setContentsMargins(0, 2, 0, 0)
        act_layout.setSpacing(4)

        btn_style = """
            QPushButton {
                background: transparent;
                color: #64748b;
                border: none;
                border-radius: 6px;
                padding: 3px 6px;
                font-size: 12px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.08);
                color: #f8fafc;
            }
        """

        self.btn_copy = QPushButton("")
        if os.path.exists(_COPY_ICON):
            self.btn_copy.setIcon(QIcon(_COPY_ICON))
            self.btn_copy.setIconSize(QSize(13, 13))
        else:
            self.btn_copy.setText("📋")
        self.btn_copy.setToolTip("Copy text")
        self.btn_copy.setCursor(Qt.PointingHandCursor)
        self.btn_copy.setStyleSheet(btn_style)
        self.btn_copy.clicked.connect(self._copy_to_clipboard)

        self.btn_retry = QPushButton("🔄")
        self.btn_retry.setToolTip("Retry")
        self.btn_retry.setCursor(Qt.PointingHandCursor)
        self.btn_retry.setStyleSheet(btn_style)
        self.btn_retry.clicked.connect(self.retry_requested.emit)

        self.btn_up = QPushButton("👍")
        self.btn_up.setToolTip("Good response")
        self.btn_up.setCursor(Qt.PointingHandCursor)
        self.btn_up.setStyleSheet(btn_style)

        self.btn_down = QPushButton("👎")
        self.btn_down.setToolTip("Bad response")
        self.btn_down.setCursor(Qt.PointingHandCursor)
        self.btn_down.setStyleSheet(btn_style)

        act_layout.addWidget(self.btn_copy)
        act_layout.addWidget(self.btn_retry)
        act_layout.addWidget(self.btn_up)
        act_layout.addWidget(self.btn_down)

        # Sources Button (if sources present)
        self.btn_sources = QPushButton()
        self.btn_sources.setCursor(Qt.PointingHandCursor)
        self.btn_sources.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.04);
                color: #94a3b8;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 6px;
                padding: 2px 8px;
                font-size: 11px;
                margin-left: 6px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.10);
                color: #f1f5f9;
            }
        """)
        self.btn_sources.clicked.connect(self._toggle_sources)
        act_layout.addWidget(self.btn_sources)
        act_layout.addStretch()

        self.main_layout.addWidget(self.actions_row)
        self.actions_row.hide()

        # 3. Collapsible Sources Container
        self.sources_card = QFrame()
        self.sources_card.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
                padding: 4px;
            }
        """)
        self.sources_layout = QVBoxLayout(self.sources_card)
        self.sources_layout.setContentsMargins(6, 6, 6, 6)
        self.sources_layout.setSpacing(4)
        self.main_layout.addWidget(self.sources_card)
        self.sources_card.hide()

        # 4. Follow-Up Suggestions
        self.follow_ups_container = QWidget()
        self.follow_ups_layout = QVBoxLayout(self.follow_ups_container)
        self.follow_ups_layout.setContentsMargins(0, 4, 0, 0)
        self.follow_ups_layout.setSpacing(4)

        lbl_header = QLabel("Follow-ups")
        lbl_header.setStyleSheet("color: #64748b; font-size: 11px; font-weight: 600; padding-left: 2px;")
        self.follow_ups_layout.addWidget(lbl_header)

        self.follow_ups_chips = QWidget()
        self.chips_layout = QVBoxLayout(self.follow_ups_chips)
        self.chips_layout.setContentsMargins(0, 0, 0, 0)
        self.chips_layout.setSpacing(4)
        self.follow_ups_layout.addWidget(self.follow_ups_chips)

        self.main_layout.addWidget(self.follow_ups_container)
        self.follow_ups_container.hide()

        # Timer for word-by-word streaming
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)

    def start_stream(self, text: str, sources: Optional[List[Dict[str, str]]] = None, follow_ups: Optional[List[str]] = None):
        """Starts streaming the provided text word by word."""
        self._full_text = text
        self._tokens = text.split() if text else []
        self._token_index = 0
        self._sources = sources or []
        self._follow_ups = follow_ups or []

        self.body_label.setText("")
        self.actions_row.hide()
        self.sources_card.hide()
        self.follow_ups_container.hide()

        if self._tokens:
            self._timer.start(self._word_ms)
        else:
            self._finish_stream()

    def set_content_immediate(self, text: str, sources: Optional[List[Dict[str, str]]] = None, follow_ups: Optional[List[str]] = None):
        """Instantly shows the complete response without streaming animation."""
        self._full_text = text
        self._sources = sources or []
        self._follow_ups = follow_ups or []
        self.body_label.setText(text)
        self._finish_stream()

    def _on_tick(self):
        if self._token_index < len(self._tokens):
            current_tokens = self._tokens[: self._token_index + 1]
            cursor_token = " ▍" if self._token_index + 1 < len(self._tokens) else ""
            self.body_label.setText(" ".join(current_tokens) + cursor_token)
            self._token_index += 1
        else:
            self._timer.stop()
            self.body_label.setText(self._full_text)
            self._finish_stream()

    def _finish_stream(self):
        # Reveal action icons
        self.actions_row.show()

        # Build sources list
        if self._sources:
            self.btn_sources.setText(f"📚 {len(self._sources)} sources")
            self.btn_sources.show()
            self._rebuild_sources()
        else:
            self.btn_sources.hide()

        # Build follow-up prompts
        if self._follow_ups:
            self._rebuild_follow_ups()
            self.follow_ups_container.show()
        else:
            self.follow_ups_container.hide()

        self.done_streaming.emit()

    def _rebuild_sources(self):
        while self.sources_layout.count():
            item = self.sources_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for s in self._sources:
            name = s.get("name", "Source")
            domain = s.get("domain", "")
            chip = QPushButton(f"🌐 {name}  •  {domain}")
            chip.setCursor(Qt.PointingHandCursor)
            chip.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 255, 255, 0.04);
                    color: #cbd5e1;
                    border: 1px solid rgba(255, 255, 255, 0.06);
                    border-radius: 6px;
                    padding: 5px 10px;
                    text-align: left;
                    font-size: 11.5px;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.09);
                    color: #ffffff;
                }
            """)
            self.sources_layout.addWidget(chip)

    def _rebuild_follow_ups(self):
        while self.chips_layout.count():
            item = self.chips_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for prompt in self._follow_ups:
            btn = QPushButton(f"↳  {prompt}")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 255, 255, 0.04);
                    color: #e2e8f0;
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    border-radius: 7px;
                    padding: 6px 10px;
                    text-align: left;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.10);
                    color: #ffffff;
                    border-color: rgba(255, 255, 255, 0.20);
                }
            """)
            btn.clicked.connect(lambda checked=False, p=prompt: self.follow_up_clicked.emit(p))
            self.chips_layout.addWidget(btn)

    def _toggle_sources(self):
        self._sources_open = not self._sources_open
        self.sources_card.setVisible(self._sources_open)

    def _copy_to_clipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self._full_text)
        if os.path.exists(_CHECK_ICON):
            self.btn_copy.setIcon(QIcon(_CHECK_ICON))
            self.btn_copy.setText("")
        else:
            self.btn_copy.setText("✓")

        def _restore():
            if os.path.exists(_COPY_ICON):
                self.btn_copy.setIcon(QIcon(_COPY_ICON))
                self.btn_copy.setText("")
            else:
                self.btn_copy.setText("📋")

        QTimer.singleShot(1200, _restore)
        self.copy_requested.emit(self._full_text)
