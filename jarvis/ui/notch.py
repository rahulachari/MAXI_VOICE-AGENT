"""
JARVIS VoiceOS Persistent Top-Center Notch HUD
Dynamic Island-style persistent top-center notch panel.
Features smooth animated expand/collapse between a subtle idle indicator pill
and a full liquid glass action card / folder browser shell.
"""

import os
from typing import Optional, List, Dict, Any
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, Signal, QPoint, QTimer, QSize
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
from PySide6.QtGui import QColor, QMouseEvent, QGuiApplication, QCursor, QIcon
from jarvis.ui.styles import NOTCH_BASE_STYLE, STATUS_CHIP_STYLE, STATUS_CHIP_DONE_STYLE
from jarvis.ui.orb import VoiceOSOrb
from jarvis.ui.waveform import SiriWaveformWidget
from jarvis.ui.action_card import ActionCard
from jarvis.ui.folder_browser import FolderBrowserWidget
from jarvis.ui.prompt_card import PromptCardWidget
from jarvis.ui.email_list_card import EmailListCardWidget
from jarvis.ui.job_card import JobCardWidget


class VoiceOSNotch(QWidget):
    clicked = Signal()
    confirmed = Signal()
    cancelled = Signal()
    close_requested = Signal()
    live_toggled = Signal(bool)

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

        # Dimensions: Curvy Top Bezel Notch (Seamless zero top gap)
        self._top_margin = 0
        self._collapsed_w = 172
        self._collapsed_h = 36
        self._expanded_w = 530
        self._normal_height = 122
        self._card_height = 300
        self._folder_height = 340
        self._prompt_card_height = 380
        self._email_card_height = 340
        self._job_card_height = 360

        # Curvy Deep Dark OLED Black Bezel Notch Container (Zero glow effects)
        self.container = QFrame(self)
        self.container.setObjectName("NotchContainer")
        self.container.setStyleSheet("""
            QFrame#NotchContainer {
                background: #000000;
                border: 1px solid #141414;
                border-top: none;
                border-top-left-radius: 0px;
                border-top-right-radius: 0px;
                border-bottom-left-radius: 24px;
                border-bottom-right-radius: 24px;
            }
        """)

        # Zero glow effects - no drop shadow or halo
        self.container.setGraphicsEffect(None)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 0, 14, 14)
        main_layout.addWidget(self.container)

        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(16, 7, 16, 10)
        self.container_layout.setSpacing(6)

        # -------------------------------------------------------------
        # 1. Collapsed Pill View (Curvy Liquid Glass Notch with Logo)
        # -------------------------------------------------------------
        self.collapsed_widget = QWidget(self.container)
        collapsed_layout = QHBoxLayout(self.collapsed_widget)
        collapsed_layout.setContentsMargins(10, 0, 10, 0)
        collapsed_layout.setSpacing(10)
        collapsed_layout.setAlignment(Qt.AlignCenter)

        # Premium Logo Emblem (Sleek Animated Orb)
        self.collapsed_orb = VoiceOSOrb(self, size=18)
        collapsed_layout.addWidget(self.collapsed_orb)

        # Siri Waveform in Pill View
        self.collapsed_waveform = SiriWaveformWidget(self.collapsed_widget, height=18)
        self.collapsed_waveform.setFixedWidth(68)
        collapsed_layout.addWidget(self.collapsed_waveform)

        self.container_layout.addWidget(self.collapsed_widget)

        # -------------------------------------------------------------
        # 2. Expanded View (Full Action Panel / Liquid Glass Shell)
        # -------------------------------------------------------------
        self.expanded_widget = QWidget(self.container)
        self.expanded_layout = QVBoxLayout(self.expanded_widget)
        self.expanded_layout.setContentsMargins(0, 0, 0, 0)
        self.expanded_layout.setSpacing(8)

        # Top Header Row (Orb + Logo on Left, Close '✕' on Top Right)
        self.header_row = QHBoxLayout()
        self.header_row.setContentsMargins(0, 0, 0, 0)
        self.header_row.setSpacing(10)
        self.header_row.setAlignment(Qt.AlignVCenter)

        # Sleek 28px Orb
        self.orb = VoiceOSOrb(self, size=28)
        self.orb.clicked.connect(self.clicked.emit)
        self.header_row.addWidget(self.orb, alignment=Qt.AlignVCenter)

        # Title Label with Logo (No "JARVIS" text)
        self.header_title = QLabel("✦")
        self.header_title.setObjectName("HeaderTitle")
        self.header_title.setStyleSheet("""
            color: #ffffff;
            font-size: 13.5px;
            font-weight: 700;
            letter-spacing: 0.04em;
            background: transparent;
        """)
        self.header_row.addWidget(self.header_title, alignment=Qt.AlignVCenter)
        self.header_row.addStretch()

        # Live Mode Toggle Button (Gemini Live with authentic gradient star icon)
        self.btn_live = QPushButton("Gemini Live", self.container)
        self.btn_live.setObjectName("NotchLiveBtn")
        self.btn_live.setToolTip("Start Live Gemini Multimodal Conversation")
        self.btn_live.setCursor(Qt.PointingHandCursor)
        self.btn_live.setCheckable(True)
        gemini_icon_path = os.path.join(os.path.dirname(__file__), "assets", "gemini_icon.svg")
        if os.path.exists(gemini_icon_path):
            self.btn_live.setIcon(QIcon(gemini_icon_path))
            self.btn_live.setIconSize(QSize(15, 15))
        self.btn_live.setStyleSheet("""
            QPushButton#NotchLiveBtn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(27, 161, 227, 0.16), stop:0.5 rgba(91, 118, 255, 0.16), stop:1 rgba(255, 99, 146, 0.16));
                color: #ffffff;
                border: 1px solid rgba(91, 118, 255, 0.45);
                font-size: 11.5px;
                font-weight: 700;
                letter-spacing: 0.03em;
                border-radius: 12px;
                padding: 0 13px;
                height: 25px;
            }
            QPushButton#NotchLiveBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(27, 161, 227, 0.32), stop:0.5 rgba(91, 118, 255, 0.32), stop:1 rgba(255, 99, 146, 0.32));
                border-color: rgba(156, 107, 255, 0.90);
                color: #ffffff;
            }
            QPushButton#NotchLiveBtn:checked {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(0, 255, 170, 0.35), stop:1 rgba(0, 200, 255, 0.35));
                color: #00ffa6;
                border: 1px solid #00ffa6;
            }
        """)
        self.btn_live.clicked.connect(self._on_live_clicked)
        self.header_row.addWidget(self.btn_live, alignment=Qt.AlignVCenter)

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
        """)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

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

        # Centered Siri & Gemini Live Fluid Waveform (Below content text at center point)
        self.waveform_row = QHBoxLayout()
        self.waveform_row.setContentsMargins(0, 4, 0, 4)
        self.waveform_row.setAlignment(Qt.AlignCenter)
        self.content_waveform = SiriWaveformWidget(self.container, height=24)
        self.content_waveform.setFixedWidth(280)
        self.waveform_row.addWidget(self.content_waveform, alignment=Qt.AlignCenter)
        self.expanded_layout.addLayout(self.waveform_row)

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

        # Embedded Autonomous Job Application Card Widget
        self.job_card = JobCardWidget(self)
        self.job_card.hide()
        self.expanded_layout.addWidget(self.job_card)

        # Footer Row (Status Pill on Left)
        self.footer_row = QHBoxLayout()
        self.footer_row.setContentsMargins(0, 4, 0, 0)
        self.footer_row.setSpacing(8)

        self.status_pill = QLabel("")
        self.status_pill.hide()

        self.pipeline_container = QWidget()
        self.pipeline_layout = QHBoxLayout(self.pipeline_container)
        self.pipeline_layout.setContentsMargins(0, 0, 0, 0)
        self.pipeline_layout.setSpacing(6)
        self.pipeline_container.hide()

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

        # Start visible docked in the middle as the minimalist camera module pill
        self.collapse_to_pill(animated=False)

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
        # header (~36px) + waveform (~28px) + footer (~28px) + padding (~36px) = ~128px
        needed = text_h + 128
        return max(self._normal_height, min(480, needed))

    def _has_persistent_card(self) -> bool:
        """Returns True if user is viewing an interactive card (Job, Prompt, Email, Folder, Action)."""
        if hasattr(self, "job_card") and self.job_card.isVisible():
            return True
        if hasattr(self, "prompt_card") and self.prompt_card.isVisible():
            return True
        if hasattr(self, "email_list_card") and self.email_list_card.isVisible():
            return True
        if hasattr(self, "folder_browser") and self.folder_browser.isVisible():
            return True
        if hasattr(self, "action_card") and self.action_card.isVisible():
            return True
        return False

    def enterEvent(self, event):
        """User is pointing or hovering mouse over the Dynamic Island: stop all auto-collapse timers!"""
        self._collapse_timer.stop()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """User moved cursor away. Only schedule auto-collapse if no interactive card is active."""
        super().leaveEvent(event)
        if self._state == "IDLE" and not self._has_persistent_card():
            self._collapse_timer.start(20000)  # Generous 20 seconds after leaving

    def collapse_to_pill(self, animated: bool = True):
        """Smoothly morphs from expanded HUD back into the minimalist curvy notch at the top."""
        self._collapse_timer.stop()
        self._is_collapsed = True
        self.action_card.hide()
        self.folder_browser.hide()
        if hasattr(self, "prompt_card"):
            self.prompt_card.hide()
        if hasattr(self, "email_list_card"):
            self.email_list_card.hide()
        if hasattr(self, "job_card"):
            self.job_card.hide()
        self.clear_pipeline()
        self.expanded_widget.hide()
        self.collapsed_widget.show()
        self.container.setStyleSheet("""
            QFrame#NotchContainer {
                background: #000000;
                border: 1px solid #141414;
                border-top: none;
                border-top-left-radius: 0px;
                border-top-right-radius: 0px;
                border-bottom-left-radius: 24px;
                border-bottom-right-radius: 24px;
            }
        """)
        self.container_layout.setContentsMargins(16, 7, 16, 10)
        self._reposition_collapsed(animated=animated)
        self.show()
        self.raise_()

    def collapse(self):
        """Dismiss notch: collapse into compact curvy top notch."""
        self.collapse_to_pill(animated=True)

    def disappear(self):
        """Completely hides the notch from screen."""
        self._collapse_timer.stop()
        self._is_collapsed = True
        self.action_card.hide()
        self.folder_browser.hide()
        if hasattr(self, "prompt_card"):
            self.prompt_card.hide()
        if hasattr(self, "email_list_card"):
            self.email_list_card.hide()
        if hasattr(self, "job_card"):
            self.job_card.hide()
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
        self.container.setStyleSheet("""
            QFrame#NotchContainer {
                background: #000000;
                border: 1px solid #141414;
                border-top: none;
                border-top-left-radius: 0px;
                border-top-right-radius: 0px;
                border-bottom-left-radius: 28px;
                border-bottom-right-radius: 28px;
            }
        """)
        self.container_layout.setContentsMargins(18, 12, 18, 14)

        geom = self._get_active_screen_geometry()
        w = self._expanded_w

        # Compute required height
        if hasattr(self, "job_card") and self.job_card.isVisible():
            h = self._job_card_height
        elif hasattr(self, "folder_browser") and self.folder_browser.isVisible():
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

    def _on_live_clicked(self, checked):
        if checked:
            self.btn_live.setText("Stop Live")
            self.orb.set_state("LISTENING")
            self.collapsed_orb.set_state("LISTENING")
            if hasattr(self, "content_waveform") and self.content_waveform:
                self.content_waveform.set_state("LISTENING")
            if hasattr(self, "collapsed_waveform") and self.collapsed_waveform:
                self.collapsed_waveform.set_state("LISTENING")
        else:
            self.btn_live.setText("Gemini Live")
            self.orb.set_state("IDLE")
            self.collapsed_orb.set_state("IDLE")
            if hasattr(self, "content_waveform") and self.content_waveform:
                self.content_waveform.set_state("IDLE")
            if hasattr(self, "collapsed_waveform") and self.collapsed_waveform:
                self.collapsed_waveform.set_state("IDLE")
        self.live_toggled.emit(checked)

    def update_energy(self, energy: float):
        if hasattr(self, "orb") and self.orb:
            self.orb.set_energy(energy)
        if hasattr(self, "collapsed_orb") and self.collapsed_orb:
            self.collapsed_orb.set_energy(energy)
        if hasattr(self, "content_waveform") and self.content_waveform:
            self.content_waveform.set_energy(energy)
        if hasattr(self, "collapsed_waveform") and self.collapsed_waveform:
            self.collapsed_waveform.set_energy(energy)

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
        self.collapsed_orb.set_state(state)
        if hasattr(self, "content_waveform") and self.content_waveform:
            self.content_waveform.set_state(state)
        if hasattr(self, "collapsed_waveform") and self.collapsed_waveform:
            self.collapsed_waveform.set_state(state)

        if state == "IDLE":
            self.header_title.setText("✦ Ready")
            # If an interactive card is open (job card, prompt card, email card), do NOT hide or auto-collapse!
            if self._has_persistent_card():
                self._collapse_timer.stop()
                return

            self.prompt_label.setText(text if text else "What can I do for you?")
            self.status_pill.setText("⚡ Ready • Hold Ctrl+Alt to speak")
            self.status_pill.show()
            self.scroll_area.show()
            if text and text != "What can I do for you?":
                needed_h = self._calculate_needed_height(text)
                self.expand(needed_h)
                # Wait indefinitely if user is pointing or copying; else give 25s
                if not self.underMouse():
                    self._collapse_timer.start(25000)
            else:
                if not self.underMouse():
                    self._collapse_timer.start(8000)

        elif state == "LISTENING":
            self._collapse_timer.stop()
            self.header_title.setText("✦ Listening...")
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
            if hasattr(self, "job_card"):
                self.job_card.hide()
            self.clear_pipeline()
            self.expand(self._normal_height)

        elif state == "PROCESSING":
            self._collapse_timer.stop()
            self.header_title.setText("✦ Thinking...")
            self.prompt_label.setText(text or "Thinking...")
            self.status_pill.setText("🔍 Processing...")
            self.status_pill.show()
            self.scroll_area.show()
            self.expand(self._normal_height)

        elif state == "EXECUTING":
            self._collapse_timer.stop()
            self.header_title.setText("✦ Executing...")
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
            self.header_title.setText("✦ Assistant")
            self.prompt_label.setText(text)
            self.status_pill.setText("⚡ Speaking...")
            self.status_pill.show()
            is_special_card = (
                (hasattr(self, "prompt_card") and self.prompt_card.isVisible())
                or (hasattr(self, "email_list_card") and self.email_list_card.isVisible())
                or (hasattr(self, "job_card") and self.job_card.isVisible())
            )
            if not is_special_card:
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
            self.header_title.setText("✕ Error")
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

    def show_job_card(self, data: Dict[str, Any]):
        """Displays autonomous job application card inside the Dynamic Island notch."""
        self._collapse_timer.stop()
        self.scroll_area.hide()
        self.action_card.hide()
        self.folder_browser.hide()
        if hasattr(self, "prompt_card"):
            self.prompt_card.hide()
        if hasattr(self, "email_list_card"):
            self.email_list_card.hide()
        job_title = data.get("job_title", "Job Application")
        self.header_title.setText(f"💼 {job_title}")
        self.job_card.display_job_application(data)
        self.job_card.show()
        match_pct = data.get("match_percentage", 96)
        self.status_pill.setText(f"🎯 {match_pct}% Match • Application Ready")
        self.show()
        self.raise_()
        self.expand(self._job_card_height)

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
        # Never collapse if user's cursor is hovering/pointing over the Dynamic Island!
        if self.underMouse():
            return
        # Never collapse if user is interacting with a card (Job, Prompt, Email, Folder)
        if self._has_persistent_card():
            return
        if self._state == "IDLE" and not self._is_collapsed:
            self.collapse_to_pill()
