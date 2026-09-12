"""
JARVIS Liquid Glass Action Card
A minimal, dark, glassmorphic floating panel matching VoiceOS design aesthetics.
Appears near the cursor when the assistant stages or confirms an action.
"""

from typing import List, Dict, Optional, Callable, Any
from PySide6.QtCore import Qt, Signal, QPoint, QTimer
from PySide6.QtWidgets import (
    QWidget,
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGraphicsDropShadowEffect,
    QApplication,
)
from PySide6.QtGui import QColor, QFont, QCursor, QScreen


# App Icons mapping (clean SVG/Unicode or fallback symbols)
APP_ICONS = {
    "gmail": "✉️",
    "email": "✉️",
    "calendar": "📅",
    "slack": "💬",
    "whatsapp": "💬",
    "reminder": "⏰",
    "task": "📝",
    "search": "🌐",
    "browser": "🌐",
    "music": "🎵",
    "spotify": "🎵",
    "youtube": "▶️",
    "settings": "⚙️",
    "default": "⚡",
}


class PillBadge(QLabel):
    """Subtle pill/chip for recognized contacts, recipients, or metadata tags."""
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QLabel {
                background: rgba(255, 255, 255, 0.10);
                color: #ffffff;
                border: 1px solid rgba(255, 255, 255, 0.14);
                border-radius: 12px;
                padding: 3px 10px;
                font-size: 13px;
                font-family: 'Segoe UI Variable Display', 'Segoe UI', -apple-system, sans-serif;
                font-weight: 500;
            }
        """)


class LiquidGlassActionCard(QFrame):
    """
    Minimal, dark, glassmorphic floating action card matching VoiceOS liquid glass UI:
    - Translucent near-black backdrop: rgba(20, 20, 24, 0.88)
    - 1px subtle light stroke: rgba(255, 255, 255, 0.10)
    - 18px rounded corners with diffuse blue outer glow
    - Form-style label + value preview rows
    - Saturated #0A6CFF pill primary action button
    """
    confirmed = Signal()
    cancelled = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LiquidGlassActionCard")
        self.setFixedWidth(360)

        # Deep dark OLED black styling (zero glow)
        self.setStyleSheet("""
            QFrame#LiquidGlassActionCard {
                background: #000000;
                border: 1px solid #1c1c1e;
                border-radius: 18px;
            }
        """)

        # Zero glow effects
        self.setGraphicsEffect(None)

        self._init_ui()

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(22, 20, 22, 20)
        self.main_layout.setSpacing(14)

        # 1. Header Row (App context indicator)
        self.header_row = QHBoxLayout()
        self.header_row.setSpacing(10)
        self.header_row.setAlignment(Qt.AlignVCenter)

        self.icon_label = QLabel("✉️")
        self.icon_label.setStyleSheet("font-size: 18px; background: transparent;")
        self.header_row.addWidget(self.icon_label)

        self.title_label = QLabel("New Message")
        self.title_label.setStyleSheet("""
            color: #ffffff;
            font-size: 14.5px;
            font-weight: 700;
            font-family: 'Segoe UI Variable Display', 'Segoe UI', -apple-system, sans-serif;
            background: transparent;
        """)
        self.header_row.addWidget(self.title_label)
        self.header_row.addStretch()

        self.main_layout.addLayout(self.header_row)

        # 1px Subtle divider below header
        self.divider = QFrame()
        self.divider.setFixedHeight(1)
        self.divider.setStyleSheet("background: rgba(255, 255, 255, 0.09); border: none;")
        self.main_layout.addWidget(self.divider)

        # 2. Form Fields Container (Preview rows)
        self.fields_container = QWidget()
        self.fields_container.setStyleSheet("background: transparent;")
        self.fields_layout = QVBoxLayout(self.fields_container)
        self.fields_layout.setContentsMargins(0, 4, 0, 4)
        self.fields_layout.setSpacing(10)
        self.main_layout.addWidget(self.fields_container)

        # 3. Action Buttons Row (Cancel & Primary Accent Pill)
        self.button_row = QHBoxLayout()
        self.button_row.setContentsMargins(0, 6, 0, 0)
        self.button_row.setSpacing(10)
        self.button_row.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.06);
                color: #94a3b8;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 14px;
                padding: 6px 16px;
                font-size: 12.5px;
                font-weight: 500;
                font-family: 'Segoe UI Variable Display', 'Segoe UI', sans-serif;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.12);
                color: #ffffff;
            }
        """)
        self.cancel_btn.clicked.connect(self._on_cancel)
        self.button_row.addWidget(self.cancel_btn)

        self.primary_btn = QPushButton("Send")
        self.primary_btn.setCursor(Qt.PointingHandCursor)
        self.primary_btn.setStyleSheet("""
            QPushButton {
                background: #0A6CFF;
                color: #ffffff;
                border: none;
                border-radius: 14px;
                padding: 6px 20px;
                font-size: 12.5px;
                font-weight: 600;
                font-family: 'Segoe UI Variable Display', 'Segoe UI', sans-serif;
            }
            QPushButton:hover {
                background: #257CFF;
            }
            QPushButton:pressed {
                background: #0056D2;
            }
        """)
        self.primary_btn.clicked.connect(self._on_confirm)
        self.button_row.addWidget(self.primary_btn)

        self.main_layout.addLayout(self.button_row)

    def set_header(self, app_name: str, action_title: str):
        """Sets the app context icon and bold title label."""
        app_key = app_name.lower().strip()
        icon = APP_ICONS.get(app_key, APP_ICONS.get("default", "⚡"))
        self.icon_label.setText(icon)
        self.title_label.setText(action_title)

    def clear_fields(self):
        """Removes all dynamic preview fields."""
        while self.fields_layout.count():
            child = self.fields_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                while child.layout().count():
                    c2 = child.layout().takeAt(0)
                    if c2.widget():
                        c2.widget().deleteLater()

    def add_field(self, label: str, value: str, is_pill: bool = False):
        """
        Adds a preview row:
        - label: muted gray label (e.g. 'To', 'Subject', 'Date')
        - value: off-white value or pill chip
        """
        row = QHBoxLayout()
        row.setSpacing(12)
        row.setAlignment(Qt.AlignTop)

        lbl = QLabel(label)
        lbl.setFixedWidth(56)
        lbl.setStyleSheet("""
            color: rgba(255, 255, 255, 0.48);
            font-size: 13px;
            font-weight: 500;
            font-family: 'Segoe UI Variable Display', 'Segoe UI', sans-serif;
            background: transparent;
        """)
        row.addWidget(lbl)

        if is_pill:
            val_pill = PillBadge(value)
            row.addWidget(val_pill)
            row.addStretch()
        else:
            val_lbl = QLabel(value)
            val_lbl.setWordWrap(True)
            val_lbl.setStyleSheet("""
                color: rgba(255, 255, 255, 0.90);
                font-size: 13.5px;
                font-family: 'Segoe UI Variable Display', 'Segoe UI', sans-serif;
                line-height: 1.45;
                background: transparent;
            """)
            row.addWidget(val_lbl, 1)

        self.fields_layout.addLayout(row)

    def configure_action(
        self,
        app_name: str,
        action_title: str,
        fields: List[Dict[str, Any]],
        primary_label: str = "Send",
        on_confirm: Optional[Callable[[], None]] = None,
        on_cancel: Optional[Callable[[], None]] = None,
    ):
        """Configures the complete card dynamically in a single call."""
        self.set_header(app_name, action_title)
        self.clear_fields()

        for f in fields:
            self.add_field(
                label=f.get("label", ""),
                value=f.get("value", ""),
                is_pill=f.get("is_pill", False),
            )

        self.primary_btn.setText(primary_label)
        if on_confirm:
            try:
                self.confirmed.disconnect()
            except Exception:
                pass
            self.confirmed.connect(on_confirm)

        if on_cancel:
            try:
                self.cancelled.disconnect()
            except Exception:
                pass
            self.cancelled.connect(on_cancel)

        self.adjustSize()

    def update_card(self, title: str, details: str, icon: str = "⚡", requires_confirmation: bool = False):
        """Compatibility method: parses details into form-style liquid glass preview rows."""
        app_name = "default"
        title_lower = (title or "").lower()
        if "email" in title_lower or "mail" in title_lower or "gmail" in title_lower:
            app_name = "gmail"
            action_title = "New Message"
        elif "calendar" in title_lower or "event" in title_lower:
            app_name = "calendar"
            action_title = "New Event"
        elif "whatsapp" in title_lower or "slack" in title_lower or "telegram" in title_lower or "message" in title_lower:
            app_name = "slack"
            action_title = "Send Message"
        elif "task" in title_lower or "todo" in title_lower or "reminder" in title_lower:
            app_name = "reminder"
            action_title = "Set Reminder"
        elif "spotify" in title_lower or "music" in title_lower:
            app_name = "spotify"
            action_title = "Play Music"
        elif "youtube" in title_lower:
            app_name = "youtube"
            action_title = "Play Video"
        else:
            action_title = title or "Action Preview"

        fields = []
        lines = [line.strip() for line in (details or "").split("\n") if line.strip()]
        for line in lines:
            if ":" in line:
                k, v = line.split(":", 1)
                is_pill = k.strip().lower() in ["to", "contact", "recipient", "date", "time", "due"]
                fields.append({"label": k.strip(), "value": v.strip(), "is_pill": is_pill})
            else:
                fields.append({"label": "Details", "value": line, "is_pill": False})

        if not fields:
            fields.append({"label": "Details", "value": details or title, "is_pill": False})

        primary_lbl = "Send" if app_name in ["gmail", "slack"] else ("Confirm ⏎" if requires_confirmation else "Open")
        self.configure_action(
            app_name=app_name,
            action_title=action_title,
            fields=fields,
            primary_label=primary_lbl,
        )

    def _on_confirm(self):
        self.confirmed.emit()

    def _on_cancel(self):
        self.cancelled.emit()


class FloatingActionOverlay(QWidget):
    """
    Standalone borderless floating window that positions the LiquidGlassActionCard
    smoothly near the user's cursor position.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint
            | Qt.FramelessWindowHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)

        self.card = LiquidGlassActionCard(self)
        self.card.confirmed.connect(self.hide)
        self.card.cancelled.connect(self.hide)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.addWidget(self.card)

    def show_near_cursor(self, cursor_pos: Optional[QPoint] = None):
        """Positions the card offset slightly from the cursor within the active screen bounds."""
        pos = cursor_pos or QCursor.pos()
        screen = QApplication.screenAt(pos) or QApplication.primaryScreen()
        geo = screen.availableGeometry()

        self.adjustSize()
        card_w = self.width()
        card_h = self.height()

        # Position slightly to the right and below the cursor
        target_x = pos.x() + 24
        target_y = pos.y() + 16

        # Avoid clipping off right edge
        if target_x + card_w > geo.right() - 20:
            target_x = max(geo.left() + 20, pos.x() - card_w - 16)

        # Avoid clipping off bottom edge
        if target_y + card_h > geo.bottom() - 20:
            target_y = max(geo.top() + 20, pos.y() - card_h - 16)

        self.move(target_x, target_y)
        self.show()
        self.raise_()


# Alias for backward compatibility
ActionCard = LiquidGlassActionCard
