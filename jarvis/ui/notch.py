"""
JARVIS VoiceOS Persistent Top-Center Notch HUD
Dynamic Island-style persistent top-center notch panel.
Features smooth animated expand/collapse between a subtle idle indicator pill
and a full liquid glass action card / folder browser shell.
"""

from typing import Optional, List, Dict, Any
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, Signal, QPoint, QTimer
from PySide6.QtWidgets import (
    QWidget,
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGraphicsDropShadowEffect,
    QScrollArea,
)
from PySide6.QtGui import QColor, QMouseEvent, QGuiApplication, QCursor
from jarvis.ui.styles import NOTCH_BASE_STYLE, STATUS_CHIP_STYLE, STATUS_CHIP_DONE_STYLE
from jarvis.ui.orb import VoiceOSOrb
from jarvis.ui.action_card import ActionCard
from jarvis.ui.folder_browser import FolderBrowserWidget
from jarvis.ui.prompt_card import PromptCardWidget
from jarvis.ui.email_list_card import EmailListCardWidget


class VoiceOSNotch(QWidget):
    clicked = Signal()
    confirmed = Signal()
    cancelled = Signal()
    close_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowFlags(
            Qt.WindowStaysOnTopHint
            | Qt.FramelessWindowHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)

        self._state = "IDLE"
        self._is_collapsed = True

        # Dimensions:
        # Dimensions:
        self._collapsed_w = 152
        self._collapsed_h = 36
        self._expanded_w = 540
        self._normal_height = 96
        self._card_height = 300
        self._folder_height = 340
        self._prompt_card_height = 380
        self._email_card_height = 340

        # Outer Shadow Frame Container (Docked flush against top of screen)
        self.container = QFrame(self)
        self.container.setObjectName("NotchContainer")
        self.container.setStyleSheet("""
            QFrame#NotchContainer {
                background: rgba(14, 16, 22, 0.96);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-top: none;
                border-bottom-left-radius: 26px;
                border-bottom-right-radius: 26px;
                border-top-left-radius: 0px;
                border-top-right-radius: 0px;
            }
        """)

        # Ambient diffuse liquid glass shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(38)
        shadow.setColor(QColor(10, 108, 255, 55))
        shadow.setOffset(0, 8)
        self.container.setGraphicsEffect(shadow)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 0, 10, 14)
        main_layout.addWidget(self.container)

        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(16, 12, 16, 12)
        self.container_layout.setSpacing(8)

        # -------------------------------------------------------------
        # 1. Collapsed Pill View (Subtle Idle Indicator)
        # -------------------------------------------------------------
        self.collapsed_widget = QWidget(self.container)
        collapsed_layout = QHBoxLayout(self.collapsed_widget)
        collapsed_layout.setContentsMargins(4, 0, 4, 0)
        collapsed_layout.setSpacing(8)
        collapsed_layout.setAlignment(Qt.AlignCenter)

        # Pulsing active status dot
        self.dot = QLabel("●")
        self.dot.setStyleSheet("color: #38bdf8; font-size: 10px; background: transparent;")
        collapsed_layout.addWidget(self.dot)

        self.collapsed_label = QLabel("JARVIS")
        self.collapsed_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.90);
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.05em;
            background: transparent;
        """)
        collapsed_layout.addWidget(self.collapsed_label)

        self.container_layout.addWidget(self.collapsed_widget)

        # -------------------------------------------------------------
        # 2. Expanded View (Full Action Panel / Liquid Glass Shell)
        # -------------------------------------------------------------
        self.expanded_widget = QWidget(self.container)
        self.expanded_layout = QVBoxLayout(self.expanded_widget)
        self.expanded_layout.setContentsMargins(0, 0, 0, 0)
        self.expanded_layout.setSpacing(8)

        # Top Header Row (Orb + Title on Left, Close '✕' on Top Right)
        self.header_row = QHBoxLayout()
        self.header_row.setContentsMargins(0, 0, 0, 0)
        self.header_row.setSpacing(10)
        self.header_row.setAlignment(Qt.AlignVCenter)

        # Sleek 28px Orb
        self.orb = VoiceOSOrb(self, size=28)
        self.orb.clicked.connect(self.clicked.emit)
        self.header_row.addWidget(self.orb, alignment=Qt.AlignVCenter)

        # Title Label
        self.header_title = QLabel("JARVIS")
        self.header_title.setObjectName("HeaderTitle")
        self.header_title.setStyleSheet("""
            color: #ffffff;
            font-size: 13.5px;
            font-weight: 700;
            letter-spacing: 0.02em;
            background: transparent;
        """)
        self.header_row.addWidget(self.header_title, alignment=Qt.AlignVCenter)
        self.header_row.addStretch()

        # Dismiss Close Button (Fixed at Top-Right Corner!)
        self.btn_close = QPushButton("✕", self.container)
        self.btn_close.setObjectName("NotchCloseBtn")
        self.btn_close.setToolTip("Close (Esc)")
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.setStyleSheet("""
            QPushButton#NotchCloseBtn {
                background: rgba(255, 255, 255, 0.08);
                color: rgba(255, 255, 255, 0.65);
                border: 1px solid rgba(255, 255, 255, 0.12);
                font-size: 11px;
                font-weight: bold;
                border-radius: 11px;
                min-width: 22px;
                max-width: 22px;
                min-height: 22px;
                max-height: 22px;
            }
            QPushButton#NotchCloseBtn:hover {
                background: rgba(255, 255, 255, 0.22);
                color: #ffffff;
                border-color: rgba(255, 255, 255, 0.25);
            }
        """)
        self.btn_close.clicked.connect(self.collapse)
        self.header_row.addWidget(self.btn_close, alignment=Qt.AlignVCenter)

        self.expanded_layout.addLayout(self.header_row)

        # Content Body: Scrollable Text Area (Guarantees zero text clipping)
        self.scroll_area = QScrollArea(self.expanded_widget)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 5px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.20);
                border-radius: 2.5px;
            }
        """)

        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 4, 4, 4)
        self.scroll_layout.setSpacing(0)

        self.prompt_label = QLabel("What can I do for you?")
        self.prompt_label.setObjectName("PromptLabel")
        self.prompt_label.setWordWrap(True)
        self.prompt_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.prompt_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.95);
            font-size: 13.5px;
            font-weight: 500;
            line-height: 1.45;
            background: transparent;
        """)
        self.scroll_layout.addWidget(self.prompt_label)
        self.scroll_area.setWidget(self.scroll_content)

        self.expanded_layout.addWidget(self.scroll_area)

        # Embedded Action Card (Email, Calendar, Messaging, Confirmations)
        self.action_card = ActionCard(self)
        self.action_card.confirmed.connect(self.confirmed.emit)
        self.action_card.cancelled.connect(self.cancelled.emit)
        self.action_card.hide()
        self.expanded_layout.addWidget(self.action_card)

        # Embedded Folder Browser Widget (Downloads, Screenshots, Desktop, etc.)
        self.folder_browser = FolderBrowserWidget(self)
        self.folder_browser.hide()
        self.expanded_layout.addWidget(self.folder_browser)

        # Embedded Prompt Card Widget (Generated Prompts with One-Click Copy)
        self.prompt_card = PromptCardWidget(self)
        self.prompt_card.hide()
        self.expanded_layout.addWidget(self.prompt_card)

        # Embedded Email List Card Widget (Gmail Inbox Summary)
        self.email_list_card = EmailListCardWidget(self)
        self.email_list_card.hide()
        self.expanded_layout.addWidget(self.email_list_card)

        # Footer Row (Status Pill on Left)
        self.footer_row = QHBoxLayout()
        self.footer_row.setContentsMargins(0, 4, 0, 0)
        self.footer_row.setSpacing(8)

        self.status_pill = QLabel("⚡ Ready • Hold Ctrl+Alt to speak")
        self.status_pill.setObjectName("StatusPill")
        self.status_pill.setStyleSheet("""
            color: rgba(255, 255, 255, 0.55);
            font-size: 12px;
            background: transparent;
        """)

        self.pipeline_container = QWidget()
        self.pipeline_layout = QHBoxLayout(self.pipeline_container)
        self.pipeline_layout.setContentsMargins(0, 0, 0, 0)
        self.pipeline_layout.setSpacing(6)
        self.pipeline_container.hide()

        self.footer_row.addWidget(self.status_pill)
        self.footer_row.addWidget(self.pipeline_container)
        self.footer_row.addStretch()

        self.expanded_layout.addLayout(self.footer_row)

        self.container_layout.addWidget(self.expanded_widget)
        self.expanded_widget.hide()

        # Geometry animation
        self.anim_geom = QPropertyAnimation(self, b"geometry")
        self.anim_geom.setDuration(220)
        self.anim_geom.setEasingCurve(QEasingCurve.OutCubic)

        # Auto-collapse timer after speech/idle
        self._collapse_timer = QTimer(self)
        self._collapse_timer.setSingleShot(True)
        self._collapse_timer.timeout.connect(self._auto_collapse)

        # Start completely hidden until hotkey Ctrl+Alt is pressed
        self._reposition_collapsed(animated=False)
        self.hide()

    def _get_active_screen_geometry(self) -> QRect:
        """Returns the geometry of the display containing the cursor or focus."""
        screen = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        return screen.availableGeometry() if screen else QRect(0, 0, 1920, 1080)

    def _reposition_collapsed(self, animated: bool = True):
        geom = self._get_active_screen_geometry()
        w = self._collapsed_w
        h = self._collapsed_h
        x = geom.x() + (geom.width() - w) // 2
        y = geom.y()

        target_rect = QRect(x, y, w, h)
        if animated and self.isVisible():
            self.anim_geom.stop()
            self.anim_geom.setStartValue(self.geometry())
            self.anim_geom.setEndValue(target_rect)
            self.anim_geom.start()
        else:
            self.setGeometry(target_rect)

    def _calculate_needed_height(self, text: str) -> int:
        """Calculates dynamic required height to prevent any text truncation or clipping."""
        if not text:
            return self._normal_height
        text_w = 480
        fm = self.prompt_label.fontMetrics()
        bounding = fm.boundingRect(QRect(0, 0, text_w, 3000), Qt.TextWordWrap, text)
        text_h = bounding.height()
        # header (~36px) + footer (~28px) + padding (~32px) + scroll margin = ~104px
        needed = text_h + 104
        return max(self._normal_height, min(440, needed))

    def collapse(self):
        """Smoothly collapses and hides the notch completely from the screen."""
        self._collapse_timer.stop()
        self._is_collapsed = True
        self.action_card.hide()
        self.folder_browser.hide()
        if hasattr(self, "prompt_card"):
            self.prompt_card.hide()
        if hasattr(self, "email_list_card"):
            self.email_list_card.hide()
        self.clear_pipeline()
        self.expanded_widget.hide()
        self.collapsed_widget.hide()
        self.hide()

    def expand(self, target_h: Optional[int] = None):
        """Smoothly expands the notch downward into the liquid glass action panel."""
        self._collapse_timer.stop()
        self._is_collapsed = False
        self.collapsed_widget.hide()
        self.expanded_widget.show()

        geom = self._get_active_screen_geometry()
        w = self._expanded_w

        # Compute required height
        if hasattr(self, "folder_browser") and self.folder_browser.isVisible():
            h = self._folder_height
        elif hasattr(self, "action_card") and self.action_card.isVisible():
            h = self._card_height
        elif hasattr(self, "prompt_card") and self.prompt_card.isVisible():
            h = self._prompt_card_height
        elif hasattr(self, "email_list_card") and self.email_list_card.isVisible():
            h = self._email_card_height
        else:
            h = target_h or self._normal_height

        x = geom.x() + (geom.width() - w) // 2
        y = geom.y()
        target_rect = QRect(x, y, w, h)

        self.anim_geom.stop()
        self.anim_geom.setStartValue(self.geometry())
        self.anim_geom.setEndValue(target_rect)
        self.anim_geom.start()

        self.show()
        self.raise_()
        self.activateWindow()

    def pop_up(self):
        """Triggered when hotkey Ctrl+Alt is pressed or listening starts."""
        self.show()
        self.raise_()
        self.activateWindow()
        self.expand(self._normal_height)

    def disappear(self):
        """Completely hides the notch from screen."""
        self.collapse()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            if self._is_collapsed:
                # Clicking when collapsed expands and triggers active session
                self.expand()
                self.clicked.emit()
                return
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.collapse()
            self.close_requested.emit()
        super().keyPressEvent(event)

    def set_state(self, state: str, text: str = ""):
        self._state = state
        self.orb.set_state(state)

        if state == "IDLE":
            self.header_title.setText("JARVIS")
            self.prompt_label.setText(text if text else "What can I do for you?")
            self.status_pill.setText("⚡ Ready • Hold Ctrl+Alt to speak")
            self.status_pill.show()
            self.scroll_area.show()
            if text and text != "What can I do for you?":
                needed_h = self._calculate_needed_height(text)
                self.expand(needed_h)
            self._collapse_timer.start(5500)

        elif state == "LISTENING":
            self._collapse_timer.stop()
            self.header_title.setText("JARVIS • Listening")
            self.prompt_label.setText(text or "Listening for your voice command...")
            self.status_pill.setText("🎙️ Listening • Release to execute")
            self.status_pill.show()
            self.scroll_area.show()
            self.action_card.hide()
            self.folder_browser.hide()
            if hasattr(self, "prompt_card"):
                self.prompt_card.hide()
            if hasattr(self, "email_list_card"):
                self.email_list_card.hide()
            self.clear_pipeline()
            self.expand(self._normal_height)

        elif state == "PROCESSING":
            self._collapse_timer.stop()
            self.header_title.setText("JARVIS • Thinking")
            self.prompt_label.setText(text or "Thinking...")
            self.status_pill.setText("🔍 Processing...")
            self.status_pill.show()
            self.scroll_area.show()
            self.expand(self._normal_height)

        elif state == "EXECUTING":
            self._collapse_timer.stop()
            self.header_title.setText("JARVIS • Executing")
            self.prompt_label.setText(text or "Performing action...")
            if self.pipeline_layout.count() > 0:
                self.status_pill.hide()
                self.pipeline_container.show()
            else:
                self.status_pill.setText("⚡ Executing ✓")
                self.status_pill.show()
            self.scroll_area.show()
            self.expand(self._normal_height)

        elif state == "SPEAKING":
            self._collapse_timer.stop()
            self.header_title.setText("JARVIS")
            self.prompt_label.setText(text)
            self.status_pill.setText("⚡ Speaking...")
            self.status_pill.show()
            if not (hasattr(self, "prompt_card") and self.prompt_card.isVisible()) and not (hasattr(self, "email_list_card") and self.email_list_card.isVisible()):
                self.scroll_area.show()
                self.action_card.hide()
                self.folder_browser.hide()
                needed_h = self._calculate_needed_height(text)
                self.expand(needed_h)
            else:
                self.expand()

        elif state == "CONFIRMATION_REQUIRED":
            self._collapse_timer.stop()
            self.header_title.setText("Confirmation Required")
            self.prompt_label.setText(text or "Safety approval required")
            self.status_pill.setText("⚠️ Confirm Action")
            self.status_pill.show()
            self.expand(self._card_height)

        elif state == "ERROR":
            self.header_title.setText("JARVIS • Error")
            self.prompt_label.setText(text or "Operation failed")
            self.status_pill.setText("✕ Failed")
            self.status_pill.show()
            self.scroll_area.show()
            needed_h = self._calculate_needed_height(text)
            self.expand(needed_h)
            self._collapse_timer.start(4500)

    def show_action_preview(self, title: str, details: str, icon: str = "⚡", requires_confirmation: bool = False):
        """Displays any action preview (Email, Calendar, WhatsApp) in the notch."""
        self._collapse_timer.stop()
        self.scroll_area.hide()
        self.folder_browser.hide()
        if hasattr(self, "prompt_card"):
            self.prompt_card.hide()
        if hasattr(self, "email_list_card"):
            self.email_list_card.hide()
        self.header_title.setText(f"{icon} {title}")
        self.action_card.update_card(title, details, icon, requires_confirmation)
        self.action_card.show()
        self.expand(self._card_height)

    def show_folder_preview(self, folder_name: str, folder_path: str, items: List[Dict[str, Any]]):
        """Displays the compact scrollable folder contents preview in the notch."""
        self._collapse_timer.stop()
        self.scroll_area.hide()
        self.action_card.hide()
        if hasattr(self, "prompt_card"):
            self.prompt_card.hide()
        if hasattr(self, "email_list_card"):
            self.email_list_card.hide()
        self.header_title.setText(f"📁 {folder_name.title()}")
        self.folder_browser.display_folder(folder_name, folder_path, items)
        self.folder_browser.show()
        self.status_pill.setText(f"📁 {len(items)} items available")
        self.expand(self._folder_height)

    def show_prompt_card(self, topic: str, prompt_text: str):
        """Displays generated prompt with one-click copy button inside the notch."""
        self._collapse_timer.stop()
        self.scroll_area.hide()
        self.action_card.hide()
        self.folder_browser.hide()
        if hasattr(self, "email_list_card"):
            self.email_list_card.hide()
        self.header_title.setText(f"🪄 Prompt: {topic.title()}")
        self.prompt_card.display_prompt(topic, prompt_text)
        self.prompt_card.show()
        self.status_pill.setText("📋 Click 'Copy Prompt' to copy to clipboard")
        self.show()
        self.raise_()
        self.expand(self._prompt_card_height)

    def show_email_list(self, emails: List[Dict[str, str]]):
        """Displays recent emails inside the notch."""
        self._collapse_timer.stop()
        self.scroll_area.hide()
        self.action_card.hide()
        self.folder_browser.hide()
        if hasattr(self, "prompt_card"):
            self.prompt_card.hide()
        self.header_title.setText(f"✉️ Gmail Inbox ({len(emails)})")
        self.email_list_card.display_emails(emails)
        self.email_list_card.show()
        self.status_pill.setText("✉️ Recent Emails")
        self.show()
        self.raise_()
        self.expand(self._email_card_height)

    def add_pipeline_step(self, label: str, icon: str, completed: bool = False, bg_color: tuple = (56, 189, 248)):
        chip = QLabel(f"{icon} {label}" + (" ✓" if completed else "..."))
        if completed:
            chip.setObjectName("StatusChipDone")
            chip.setStyleSheet(STATUS_CHIP_DONE_STYLE)
        else:
            chip.setObjectName("StatusChip")
            r, g, b = bg_color
            chip.setStyleSheet(STATUS_CHIP_STYLE.replace("{bg_r}", str(r)).replace("{bg_g}", str(g)).replace("{bg_b}", str(b)).replace("{font}", "'Cascadia Code', 'DM Mono', monospace"))

        self.pipeline_layout.addWidget(chip)
        if self._state == "EXECUTING":
            self.status_pill.hide()
            self.pipeline_container.show()

    def clear_pipeline(self):
        while self.pipeline_layout.count():
            item = self.pipeline_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.pipeline_container.hide()

    def update_energy(self, energy: float):
        self.orb.set_energy(energy)

    def set_mode(self, mode: str):
        pass

    def _auto_collapse(self):
        if self._state == "IDLE" and not self._is_collapsed:
            self.collapse()
