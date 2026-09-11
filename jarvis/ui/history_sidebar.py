"""
JARVIS VoiceOS History Sidebar
Left-edge sliding glass panel matching VoiceOS design — app icon badges,
searchable history, timestamped sessions, and new-chat button.
"""

from typing import Optional
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QFrame,
    QApplication,
    QGraphicsDropShadowEffect,
)
from PySide6.QtGui import QColor, QFont
from jarvis.ui.monitor_helper import get_active_monitor_geometry
from jarvis.storage.history_repository import HistoryRepository

# App icon emoji mapping for history items
APP_ICONS = {
    "APP_LAUNCH": "🚀",
    "APP_CLOSE": "✖️",
    "APP_FOCUS": "🔲",
    "WEB_NAVIGATION": "🌐",
    "WEB_SEARCH": "🔍",
    "BROWSER_ACTION": "🌐",
    "FILE_SEARCH": "📁",
    "FILE_OPEN": "📂",
    "FILE_CREATE": "📄",
    "FILE_DELETE": "🗑️",
    "MESSAGING": "💬",
    "EMAIL": "📧",
    "PHONE_CALL": "📞",
    "MEDIA_CONTROL": "🎵",
    "MUSIC": "🎶",
    "SYSTEM_CONTROL": "⚙️",
    "SCREENSHOT": "📸",
    "KEYBOARD_SHORTCUT": "⌨️",
    "SCREEN_ANALYSIS": "👁️",
    "CURSOR_ANALYSIS": "👆",
    "DICTATION": "✏️",
    "AI_QUERY": "🤖",
    "REMINDER": "⏰",
    "CALENDAR": "📅",
    "TASK": "✅",
    "MEMORY": "🧠",
    "CANCEL": "🚫",
}

# App-specific badge colors
APP_COLORS = {
    "EMAIL": "#EA4335",
    "MESSAGING": "#25D366",
    "WEB_SEARCH": "#4285F4",
    "WEB_NAVIGATION": "#4285F4",
    "FILE_SEARCH": "#FF9500",
    "FILE_OPEN": "#FF9500",
    "APP_LAUNCH": "#7C3AED",
    "MEDIA_CONTROL": "#1DB954",
    "SYSTEM_CONTROL": "#64748B",
    "AI_QUERY": "#06B6D4",
    "CALENDAR": "#4285F4",
    "TASK": "#10B981",
    "MEMORY": "#8B5CF6",
}

SIDEBAR_STYLE = """
QWidget#SidebarContainer {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 rgba(8, 10, 16, 0.97),
        stop:0.85 rgba(12, 15, 22, 0.96),
        stop:1 rgba(18, 22, 32, 0.94));
    border-right: 1px solid rgba(255, 255, 255, 0.10);
}

QLineEdit#SearchInput {
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 12px;
    color: #ffffff;
    padding: 9px 14px 9px 36px;
    font-size: 13px;
    font-family: 'Segoe UI Variable Display', 'Segoe UI', -apple-system, sans-serif;
}
QLineEdit#SearchInput:focus {
    border: 1px solid rgba(255, 255, 255, 0.35);
    background: rgba(255, 255, 255, 0.09);
}
QLineEdit#SearchInput::placeholder {
    color: rgba(148, 163, 184, 0.7);
}

QScrollArea {
    border: none;
    background: transparent;
}

QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 5px;
    margin: 4px 1px;
}
QScrollBar::handle:vertical {
    background: rgba(255, 255, 255, 0.15);
    border-radius: 2px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: rgba(255, 255, 255, 0.30);
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}
"""


class HistorySidebar(QWidget):
    run_again_requested = Signal(str)

    def __init__(self, history_repo: Optional[HistoryRepository] = None, parent=None):
        super().__init__(parent)
        self.repo = history_repo or HistoryRepository()

        self.setWindowFlags(
            Qt.WindowStaysOnTopHint
            | Qt.FramelessWindowHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._width = 340
        self._is_visible = False

        # Container
        self.container = QWidget(self)
        self.container.setObjectName("SidebarContainer")
        self.container.setStyleSheet(SIDEBAR_STYLE)

        # Edge shadow for depth
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(6, 0)
        self.container.setGraphicsEffect(shadow)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.container)

        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(14, 16, 14, 16)
        container_layout.setSpacing(10)

        # ── Header Row: New Chat + Close ──
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(4, 0, 4, 0)

        self.btn_new_chat = QPushButton("＋")
        self.btn_new_chat.setToolTip("New session")
        self.btn_new_chat.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.06);
                color: #94a3b8;
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 10px;
                font-size: 16px;
                font-weight: 300;
                padding: 4px 10px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.12);
                color: #ffffff;
                border-color: rgba(255, 255, 255, 0.25);
            }
        """)
        self.btn_new_chat.clicked.connect(self._on_new_session)

        self.btn_close = QPushButton("✕")
        self.btn_close.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #64748b;
                border: none;
                font-size: 14px;
                padding: 4px 8px;
            }
            QPushButton:hover { color: #f1f5f9; }
        """)
        self.btn_close.clicked.connect(self.hide_sidebar)

        header_layout.addWidget(self.btn_new_chat)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_close)
        container_layout.addLayout(header_layout)

        # ── Search Box with icon ──
        search_container = QWidget()
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(0)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("SearchInput")
        self.search_input.setPlaceholderText("Search")
        self.search_input.textChanged.connect(self.refresh_history)

        # Search icon overlay
        self.search_icon = QLabel("🔍", self.search_input)
        self.search_icon.setStyleSheet("color: #64748b; font-size: 13px; background: transparent; border: none;")
        self.search_icon.move(12, 8)

        search_layout.addWidget(self.search_input)
        container_layout.addWidget(search_container)

        # ── Scroll Area for History Items ──
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(2, 4, 2, 4)
        self.scroll_layout.setSpacing(2)
        self.scroll_layout.addStretch()

        self.scroll_area.setWidget(self.scroll_content)
        container_layout.addWidget(self.scroll_area)

        # Animation
        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(280)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)

    def toggle(self):
        if self._is_visible:
            self.hide_sidebar()
        else:
            self.show_sidebar()

    def show_sidebar(self):
        self._is_visible = True
        mon = get_active_monitor_geometry()
        h = mon.height()
        y = mon.y()
        start_rect = QRect(mon.x() - self._width, y, self._width, h)
        end_rect = QRect(mon.x(), y, self._width, h)

        self.refresh_history()
        self.show()
        self.raise_()

        self.anim.stop()
        self.anim.setStartValue(start_rect)
        self.anim.setEndValue(end_rect)
        self.anim.start()

    def hide_sidebar(self):
        self._is_visible = False
        mon = get_active_monitor_geometry()
        h = mon.height()
        y = mon.y()
        end_rect = QRect(mon.x() - self._width, y, self._width, h)

        self.anim.stop()
        self.anim.setStartValue(self.geometry())
        self.anim.setEndValue(end_rect)

        try:
            self.anim.finished.disconnect()
        except Exception:
            pass
        self.anim.finished.connect(self._on_hide_finished)
        self.anim.start()

    def _on_hide_finished(self):
        try:
            self.anim.finished.disconnect(self._on_hide_finished)
        except Exception:
            pass
        self.hide()

    def _on_new_session(self):
        """Starts a new voice session."""
        self.repo._current_session_id = None
        self.refresh_history()

    def refresh_history(self):
        # Clear existing item widgets
        while self.scroll_layout.count() > 1:
            child = self.scroll_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        query = self.search_input.text()
        grouped = self.repo.get_grouped_history(query)

        has_items = False
        for group_name in ["TODAY", "YESTERDAY", "THIS WEEK", "OLDER"]:
            items = grouped.get(group_name, [])
            if not items:
                continue

            has_items = True
            # Section timestamp label
            sec_header = QLabel(group_name.capitalize() if group_name != "THIS WEEK" else "This Week")
            sec_header.setStyleSheet(
                "color: #475569; font-size: 11px; font-weight: 600; "
                "letter-spacing: 0.3px; padding: 8px 6px 3px 6px;"
            )
            self.scroll_layout.insertWidget(self.scroll_layout.count() - 1, sec_header)

            for item in items:
                card = self._create_item_card(item)
                self.scroll_layout.insertWidget(self.scroll_layout.count() - 1, card)

        if not has_items:
            empty_lbl = QLabel("No history yet")
            empty_lbl.setAlignment(Qt.AlignCenter)
            empty_lbl.setStyleSheet(
                "color: #475569; font-size: 13px; margin-top: 60px; "
                "font-family: 'Segoe UI Variable Display', 'Segoe UI', sans-serif;"
            )
            self.scroll_layout.insertWidget(0, empty_lbl)

    def _create_item_card(self, item: dict) -> QWidget:
        """Creates a VoiceOS-style task card with app icon badge."""
        card = QFrame()
        card.setCursor(Qt.PointingHandCursor)

        tool_name = item.get("tool", "AI_QUERY")
        badge_color = APP_COLORS.get(tool_name, "#64748B")
        icon = APP_ICONS.get(tool_name, "🤖")
        status = item.get("status", "SUCCESS")

        # Status dot color
        dot_color = "#3B82F6" if status == "SUCCESS" else "#F59E0B" if status == "REQUIRES_CONFIRMATION" else "#EF4444"

        card.setStyleSheet(f"""
            QFrame {{
                background: transparent;
                border: none;
                border-radius: 10px;
                padding: 2px;
            }}
            QFrame:hover {{
                background: rgba(255, 255, 255, 0.04);
            }}
        """)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(8, 7, 8, 7)
        layout.setSpacing(10)

        # App icon badge (colored circle with emoji)
        icon_badge = QLabel(icon)
        icon_badge.setFixedSize(28, 28)
        icon_badge.setAlignment(Qt.AlignCenter)
        icon_badge.setStyleSheet(f"""
            background: {badge_color}22;
            border-radius: 14px;
            font-size: 13px;
            border: none;
        """)
        layout.addWidget(icon_badge)

        # Text content
        text_layout = QVBoxLayout()
        text_layout.setSpacing(1)
        text_layout.setContentsMargins(0, 0, 0, 0)

        cmd_text = item.get("command", "")
        if len(cmd_text) > 32:
            cmd_text = cmd_text[:30] + "..."

        cmd_lbl = QLabel(cmd_text)
        cmd_lbl.setStyleSheet(
            "color: #e2e8f0; font-weight: 500; font-size: 12.5px; border: none; "
            "font-family: 'Segoe UI Variable Display', 'Segoe UI', sans-serif;"
        )

        text_layout.addWidget(cmd_lbl)
        layout.addLayout(text_layout, stretch=1)

        # Status dot + time
        right_layout = QVBoxLayout()
        right_layout.setSpacing(2)
        right_layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Status dot
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {dot_color}; font-size: 7px; border: none;")
        dot.setAlignment(Qt.AlignRight)
        right_layout.addWidget(dot)

        layout.addLayout(right_layout)

        # Click to re-run
        cmd_full = item.get("command", "")
        card.mousePressEvent = lambda e, c=cmd_full: self._on_run_again(c) if e.button() == Qt.LeftButton else None

        return card

    def _on_run_again(self, command: str):
        self.hide_sidebar()
        self.run_again_requested.emit(command)

    def _copy_command(self, command: str):
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(command)

    def _delete_item(self, user_msg_id: str):
        if user_msg_id:
            self.repo.delete_item(user_msg_id)
            self.refresh_history()

