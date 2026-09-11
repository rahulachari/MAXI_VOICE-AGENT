"""
JARVIS VoiceOS Chat Composer & Conversation Panel
Interactive panel featuring context tabs, scripted agent reply sections with
reasoning breakdowns & execution time, right-aligned user bubbles,
and an interactive bottom composer with send trigger.
"""

from typing import List, Dict, Optional, Callable
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QWidget,
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
)
from PySide6.QtGui import QCursor, QFont
from jarvis.ui.streaming_text import StreamingTextWidget


class ChatMessageBubble(QWidget):
    """User speech / text bubble, right-aligned."""
    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(40, 2, 4, 2)
        layout.setSpacing(0)

        layout.addStretch()

        bubble = QLabel(text)
        bubble.setWordWrap(True)
        bubble.setTextInteractionFlags(Qt.TextSelectableByMouse)
        bubble.setStyleSheet("""
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.12);
            color: #ffffff;
            font-size: 13px;
            padding: 8px 14px;
            border-radius: 14px;
            border-bottom-right-radius: 4px;
            font-family: 'Segoe UI Variable Display', 'Segoe UI', sans-serif;
        """)
        layout.addWidget(bubble)


class AssistantSection(QWidget):
    """Structured assistant reply section with header label, sub, duration, and body."""
    def __init__(
        self,
        label: str,
        sub: str,
        time_str: str,
        body: str,
        sources: Optional[List[Dict[str, str]]] = None,
        follow_ups: Optional[List[str]] = None,
        parent=None,
    ):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Header: Label • Sub • for 2s
        hdr = QHBoxLayout()
        hdr.setSpacing(6)

        lbl = QLabel(label)
        lbl.setStyleSheet("color: #38bdf8; font-size: 11.5px; font-weight: 600;")

        sub_lbl = QLabel(sub)
        sub_lbl.setStyleSheet("color: #64748b; font-size: 11.5px;")

        time_lbl = QLabel(f"for {time_str}")
        time_lbl.setStyleSheet("color: #475569; font-size: 10.5px; font-family: monospace;")

        hdr.addWidget(lbl)
        hdr.addWidget(sub_lbl)
        hdr.addWidget(time_lbl)
        hdr.addStretch()
        layout.addLayout(hdr)

        # Body: StreamingTextWidget for rich citations, action icons, and follow-ups
        self.stream_widget = StreamingTextWidget(
            text=body,
            sources=sources,
            follow_ups=follow_ups,
            parent=self,
        )
        self.stream_widget.set_content_immediate(body, sources, follow_ups)
        layout.addWidget(self.stream_widget)


class ChatComposerPanel(QWidget):
    """
    Complete VoiceOS Chat Composer & Thread Panel.
    Can be used standalone or embedded in the sidebar.
    """
    message_sent = Signal(str)
    new_chat_requested = Signal()
    follow_up_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._tabs = ["General", "Terminal", "Knowledge", "Apps"]
        self._current_tab = "General"

        self._init_ui()

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # ── 1. Header: Context Tabs + Quick Actions ──
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.02);
                border-bottom: 1px solid rgba(255, 255, 255, 0.07);
                padding: 4px;
            }
        """)
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(8, 4, 8, 4)
        h_layout.setSpacing(6)

        # Tabs
        self.tab_buttons: Dict[str, QPushButton] = {}
        for tab in self._tabs:
            btn = QPushButton(tab)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked=False, t=tab: self._set_active_tab(t))
            h_layout.addWidget(btn)
            self.tab_buttons[tab] = btn

        self._update_tab_styles()
        h_layout.addStretch()

        # Action Buttons
        self.btn_new = QPushButton("＋")
        self.btn_new.setToolTip("New Chat")
        self.btn_new.setCursor(Qt.PointingHandCursor)
        self.btn_new.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.05);
                color: #94a3b8;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 6px;
                font-size: 14px;
                padding: 2px 8px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.12);
                color: #ffffff;
            }
        """)
        self.btn_new.clicked.connect(self.new_chat_requested.emit)
        h_layout.addWidget(self.btn_new)

        self.main_layout.addWidget(header)

        # ── 2. Scroll Area for Message Thread ──
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 5px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.15);
                border-radius: 2px;
            }
        """)

        self.thread_container = QWidget()
        self.thread_layout = QVBoxLayout(self.thread_container)
        self.thread_layout.setContentsMargins(10, 10, 10, 10)
        self.thread_layout.setSpacing(10)
        self.thread_layout.addStretch()

        self.scroll_area.setWidget(self.thread_container)
        self.main_layout.addWidget(self.scroll_area, 1)

        # ── 3. Bottom Composer Box ──
        composer_container = QWidget()
        composer_container.setStyleSheet("background: transparent; padding: 6px;")
        comp_layout = QHBoxLayout(composer_container)
        comp_layout.setContentsMargins(4, 4, 4, 4)
        comp_layout.setSpacing(6)

        # Input Frame
        input_frame = QFrame()
        input_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 12px;
                padding: 2px 6px;
            }
            QFrame:focus-within {
                border-color: rgba(255, 255, 255, 0.28);
                background: rgba(255, 255, 255, 0.08);
            }
        """)
        in_layout = QHBoxLayout(input_frame)
        in_layout.setContentsMargins(8, 4, 4, 4)
        in_layout.setSpacing(6)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Prompt or ask JARVIS...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: #ffffff;
                font-size: 13px;
                font-family: 'Segoe UI Variable Display', 'Segoe UI', sans-serif;
            }
            QLineEdit::placeholder { color: #64748b; }
        """)
        self.input_field.returnPressed.connect(self._on_send)
        self.input_field.textChanged.connect(self._on_text_changed)

        self.btn_send = QPushButton("↑")
        self.btn_send.setCursor(Qt.PointingHandCursor)
        self.btn_send.setEnabled(False)
        self.btn_send.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.10);
                color: #64748b;
                border: none;
                border-radius: 8px;
                min-width: 28px;
                max-width: 28px;
                min-height: 28px;
                max-height: 28px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:enabled {
                background: #ffffff;
                color: #0f172a;
            }
            QPushButton:enabled:hover {
                background: #f1f5f9;
            }
        """)
        self.btn_send.clicked.connect(self._on_send)

        in_layout.addWidget(self.input_field, 1)
        in_layout.addWidget(self.btn_send)

        comp_layout.addWidget(input_frame)
        self.main_layout.addWidget(composer_container)

    def add_user_message(self, text: str):
        bubble = ChatMessageBubble(text, self.thread_container)
        # Insert before stretch
        self.thread_layout.insertWidget(self.thread_layout.count() - 1, bubble)
        self._scroll_to_bottom()

    def add_assistant_message(
        self,
        label: str = "JARVIS Response",
        sub: str = "AI Engine",
        time_str: str = "1s",
        body: str = "",
        sources: Optional[List[Dict[str, str]]] = None,
        follow_ups: Optional[List[str]] = None,
    ):
        section = AssistantSection(label, sub, time_str, body, sources, follow_ups, self.thread_container)
        section.stream_widget.follow_up_clicked.connect(self.follow_up_selected.emit)
        self.thread_layout.insertWidget(self.thread_layout.count() - 1, section)
        self._scroll_to_bottom()

    def clear_messages(self):
        while self.thread_layout.count() > 1:
            item = self.thread_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _set_active_tab(self, tab: str):
        self._current_tab = tab
        self._update_tab_styles()

    def _update_tab_styles(self):
        for name, btn in self.tab_buttons.items():
            if name == self._current_tab:
                btn.setStyleSheet("""
                    QPushButton {
                        background: rgba(255, 255, 255, 0.12);
                        color: #ffffff;
                        border: 1px solid rgba(255, 255, 255, 0.20);
                        border-radius: 6px;
                        padding: 3px 10px;
                        font-size: 11.5px;
                        font-weight: 500;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background: transparent;
                        color: #64748b;
                        border: none;
                        border-radius: 6px;
                        padding: 3px 10px;
                        font-size: 11.5px;
                    }
                    QPushButton:hover {
                        background: rgba(255, 255, 255, 0.05);
                        color: #cbd5e1;
                    }
                """)

    def _on_text_changed(self, text: str):
        self.btn_send.setEnabled(bool(text.strip()))

    def _on_send(self):
        text = self.input_field.text().strip()
        if not text:
            return
        self.input_field.clear()
        self.add_user_message(text)
        self.message_sent.emit(text)

    def _scroll_to_bottom(self):
        QTimer.singleShot(50, lambda: self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        ))
