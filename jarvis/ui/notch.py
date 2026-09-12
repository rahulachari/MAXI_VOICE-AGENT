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
from PySide6.QtGui import (
    QColor,
    QMouseEvent,
    QGuiApplication,
    QCursor,
    QIcon,
    QPainter,
    QPainterPath,
    QLinearGradient,
    QPen,
    QBrush,
)
from jarvis.ui.styles import NOTCH_BASE_STYLE, STATUS_CHIP_STYLE, STATUS_CHIP_DONE_STYLE
from jarvis.ui.orb import VoiceOSOrb
from jarvis.ui.waveform import SiriWaveformWidget
from jarvis.ui.action_card import ActionCard
from jarvis.ui.folder_browser import FolderBrowserWidget
from jarvis.ui.prompt_card import PromptCardWidget
from jarvis.ui.email_list_card import EmailListCardWidget
from jarvis.ui.job_card import JobCardWidget

_ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
_COPY_ICON = os.path.join(_ASSETS_DIR, "copy_icon.svg")
_CHECK_ICON = os.path.join(_ASSETS_DIR, "check_icon.svg")
_SPEAKER_ICON = os.path.join(_ASSETS_DIR, "speaker_icon.svg")
_MUTE_ICON = os.path.join(_ASSETS_DIR, "mute_icon.svg")


class LiquidGlassContainer(QFrame):
    """Liquid Glass Container modeled after Image 2: glassmorphism aesthetic with frosted glass panels,
    soft natural lighting, muted earth/gray/cement tones, and high-transparency layering."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("NotchContainer")
        self._is_collapsed = True
        self._radius = 20.0

    def set_collapsed(self, collapsed: bool):
        self._is_collapsed = collapsed
        self._radius = 18.0 if collapsed else 26.0
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        w = float(self.width())
        h = float(self.height())
        r = float(self._radius)

        # 1. Glass Body Path: iPhone Dynamic Island capsule when collapsed; liquid action card when expanded
        path = QPainterPath()
        if self._is_collapsed:
            r = h / 2.0
            path.addRoundedRect(0.0, 0.0, w, h, r, r)
        else:
            path.moveTo(0, 0)
            path.lineTo(w, 0)
            path.lineTo(w, h - r)
            # Continuous curvature bottom-right (Apple squircle)
            path.cubicTo(w, h - r * 0.448, w - r * 0.448, h, w - r, h)
            path.lineTo(r, h)
            # Continuous curvature bottom-left
            path.cubicTo(r * 0.448, h, 0, h - r * 0.448, 0, h - r)
            path.closeSubpath()

        # 2. Transparent Frosted Glass Background
        bg_grad = QLinearGradient(0, 0, 0, h)
        if self._is_collapsed:
            bg_grad.setColorAt(0.0, QColor(14, 16, 22, 235))
            bg_grad.setColorAt(1.0, QColor(6, 8, 11, 245))
        else:
            bg_grad.setColorAt(0.0, QColor(42, 45, 52, 160))
            bg_grad.setColorAt(0.40, QColor(28, 31, 37, 175))
            bg_grad.setColorAt(1.0, QColor(18, 20, 25, 185))
        painter.fillPath(path, bg_grad)

        # 3. Soft Natural Lighting Sheen (Only in expanded panel)
        if not self._is_collapsed:
            painter.save()
            painter.setClipPath(path)
            sheen_h = min(h * 0.45, 60.0)
            sheen_grad = QLinearGradient(0, 0, 0, sheen_h)
            sheen_grad.setColorAt(0.0, QColor(255, 255, 255, 55))
            sheen_grad.setColorAt(0.40, QColor(255, 255, 255, 18))
            sheen_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
            painter.fillPath(path, sheen_grad)
            painter.restore()

        # 4. Specular Refraction Contour (Expanded panel only)
        if not self._is_collapsed:
            down_edge = QPainterPath()
            down_edge.moveTo(0, h - r)
            down_edge.cubicTo(0, h - r * 0.448, r * 0.448, h, r, h)
            down_edge.lineTo(w - r, h)
            down_edge.cubicTo(w - r * 0.448, h, w, h - r * 0.448, w, h - r)

            spec_grad = QLinearGradient(0, 0, w, 0)
            spec_grad.setColorAt(0.0, QColor(255, 255, 255, 25))
            spec_grad.setColorAt(0.25, QColor(226, 232, 240, 70))
            spec_grad.setColorAt(0.50, QColor(255, 255, 255, 140))
            spec_grad.setColorAt(0.75, QColor(226, 232, 240, 70))
            spec_grad.setColorAt(1.0, QColor(255, 255, 255, 25))

            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(spec_grad, 1.2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.drawPath(down_edge)

        # 5. Hairline Outer Boundary Stroke
        outer_rim = QLinearGradient(0, 0, 0, h)
        if self._is_collapsed:
            outer_rim.setColorAt(0.0, QColor(255, 255, 255, 45))
            outer_rim.setColorAt(1.0, QColor(255, 255, 255, 18))
            painter.setPen(QPen(outer_rim, 0.9))
        else:
            outer_rim.setColorAt(0.0, QColor(255, 255, 255, 70))
            outer_rim.setColorAt(0.5, QColor(255, 255, 255, 25))
            outer_rim.setColorAt(1.0, QColor(255, 255, 255, 45))
            painter.setPen(QPen(outer_rim, 1.0))
        painter.drawPath(path)


class VoiceOSNotch(QWidget):
    clicked = Signal()
    confirmed = Signal()
    cancelled = Signal()
    close_requested = Signal()
    live_toggled = Signal(bool)
    voice_mute_toggled = Signal(bool)
    copy_clicked = Signal(str)

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
        self._voice_active = False

        # Dimensions: Ultra-sleek iPhone 18 Pro Dynamic Island Capsule
        self._top_margin = 4
        self._collapsed_w = 104
        self._collapsed_h = 24
        self._expanded_w = 540
        self._normal_height = 140
        self._card_height = 300
        self._folder_height = 340
        self._prompt_card_height = 380
        self._email_card_height = 340
        self._job_card_height = 360

        # Curvy OLED Pitch-Black & MacBook Liquid Glass Container
        self.container = LiquidGlassContainer(self)
        self.container.setObjectName("NotchContainer")
        self.container.setStyleSheet("""
            QFrame#NotchContainer {
                background: transparent;
                border: none;
            }
        """)

        # Ambient floating drop shadow for Apple hardware depth
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(0, 0, 0, 190))
        shadow.setOffset(0, 4)
        self.container.setGraphicsEffect(shadow)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 0, 4, 6)
        main_layout.addWidget(self.container)

        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(10, 2, 10, 2)
        self.container_layout.setSpacing(0)

        # -------------------------------------------------------------
        # 1. Collapsed View: iPhone 18 Pro Dynamic Island Minimalist Capsule
        # -------------------------------------------------------------
        self.collapsed_widget = QWidget(self.container)
        collapsed_layout = QHBoxLayout(self.collapsed_widget)
        collapsed_layout.setContentsMargins(4, 0, 4, 0)
        collapsed_layout.setSpacing(0)
        collapsed_layout.setAlignment(Qt.AlignVCenter)

        # Minimalist TrueDepth camera sensor lens dot on the left
        self.camera_dot = QWidget(self.collapsed_widget)
        self.camera_dot.setFixedSize(7, 7)
        self.camera_dot.setStyleSheet("""
            background: qradialgradient(cx:0.4, cy:0.4, radius:0.75, fx:0.3, fy:0.3,
                stop:0 rgba(255, 255, 255, 0.40),
                stop:0.55 rgba(30, 41, 59, 0.95),
                stop:1.0 rgba(10, 15, 25, 1.0));
            border: 1px solid rgba(255, 255, 255, 0.18);
            border-radius: 3.5px;
        """)
        collapsed_layout.addWidget(self.camera_dot, alignment=Qt.AlignVCenter)

        collapsed_layout.addStretch()

        # Subtle mic activity indicator dot on the right
        self.activity_dot = QWidget(self.collapsed_widget)
        self.activity_dot.setFixedSize(5, 5)
        self.activity_dot.setStyleSheet("""
            background: rgba(255, 255, 255, 0.20);
            border-radius: 2.5px;
        """)
        collapsed_layout.addWidget(self.activity_dot, alignment=Qt.AlignVCenter)

        self.container_layout.addWidget(self.collapsed_widget)

        # -------------------------------------------------------------
        # 2. Expanded View (Full Action Panel / Liquid Glass Shell)
        # -------------------------------------------------------------
        self.expanded_widget = QWidget(self.container)
        self.expanded_layout = QVBoxLayout(self.expanded_widget)
        self.expanded_layout.setContentsMargins(0, 0, 0, 0)
        self.expanded_layout.setSpacing(8)

        # Top Header Row (Liquid Orb Gemini AI Button + Title on Left, Close on Right)
        self.header_row = QHBoxLayout()
        self.header_row.setContentsMargins(0, 0, 0, 0)
        self.header_row.setSpacing(10)
        self.header_row.setAlignment(Qt.AlignVCenter)

        # Gemini AI Button (Living Liquid Orb Animation)
        self.orb = VoiceOSOrb(self, size=28)
        self.orb.setToolTip("JARVIS • Click to start/stop Daemon Live conversation")
        self.orb.clicked.connect(self._on_orb_clicked)
        self.header_row.addWidget(self.orb, alignment=Qt.AlignVCenter)

        # Title Label with Metallic Logo
        self.header_title = QLabel("✦ JARVIS")
        self.header_title.setObjectName("HeaderTitle")
        self.header_title.setStyleSheet("""
            color: #f1f5f9;
            font-size: 13.5px;
            font-weight: 700;
            letter-spacing: 0.03em;
            background: transparent;
        """)
        self.header_row.addWidget(self.header_title, alignment=Qt.AlignVCenter)
        self.header_row.addStretch()

        # Dismiss Close Button (Minimalist Apple Frosted Circular Button)
        self.btn_close = QPushButton("✕", self.container)
        self.btn_close.setObjectName("NotchCloseBtn")
        self.btn_close.setToolTip("Close (Esc)")
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.setStyleSheet("""
            QPushButton#NotchCloseBtn {
                background: rgba(255, 255, 255, 0.06);
                color: rgba(241, 245, 249, 0.7);
                border: 1px solid rgba(255, 255, 255, 0.12);
                font-size: 10px;
                font-weight: bold;
                border-radius: 11px;
                min-width: 22px;
                max-width: 22px;
                min-height: 22px;
                max-height: 22px;
            }
            QPushButton#NotchCloseBtn:hover {
                background: rgba(239, 68, 68, 0.35);
                color: #ffffff;
                border-color: rgba(239, 68, 68, 0.60);
            }
        """)
        self.btn_close.clicked.connect(self._on_close_clicked)
        self.header_row.addWidget(self.btn_close, alignment=Qt.AlignVCenter)

        self.expanded_layout.addLayout(self.header_row)

        # Content Body: Scrollable Text Area (Zero bars visible, auto-height expansion)
        self.scroll_area = QScrollArea(self.expanded_widget)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical, QScrollBar:horizontal {
                width: 0px;
                height: 0px;
                background: transparent;
                border: none;
            }
            QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
                width: 0px;
                height: 0px;
                background: transparent;
                border: none;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
                height: 0px;
                background: transparent;
                border: none;
            }
        """)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(2, 2, 4, 4)
        self.scroll_layout.setSpacing(0)

        self.prompt_label = QLabel("What can I do for you?")
        self.prompt_label.setObjectName("PromptLabel")
        self.prompt_label.setWordWrap(True)
        self.prompt_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.prompt_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.prompt_label.setStyleSheet("""
            color: #f8fafc;
            font-size: 14px;
            font-weight: 450;
            background: transparent;
            padding: 2px 2px;
            text-align: left;
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

        # Embedded Autonomous Job Application Card Widget
        self.job_card = JobCardWidget(self)
        self.job_card.hide()
        self.expanded_layout.addWidget(self.job_card)

        # Footer Row (Status Pill on Left, Copy & Voice Controls on Right - Ultra-Transparent Cement Logos)
        self.footer_row = QHBoxLayout()
        self.footer_row.setContentsMargins(0, 4, 0, 2)
        self.footer_row.setSpacing(8)

        self.status_pill = QLabel("")
        self.status_pill.setObjectName("StatusPill")
        self.status_pill.hide()

        self.pipeline_container = QWidget()
        self.pipeline_layout = QHBoxLayout(self.pipeline_container)
        self.pipeline_layout.setContentsMargins(0, 0, 0, 0)
        self.pipeline_layout.setSpacing(6)
        self.pipeline_container.hide()

        self.footer_row.addWidget(self.status_pill)
        self.footer_row.addWidget(self.pipeline_container)
        self.footer_row.addStretch()

        # Action Buttons Container (Ultra-Transparent Frosted Glass Logos - No text names)
        self.action_btn_container = QWidget()
        self.action_btn_layout = QHBoxLayout(self.action_btn_container)
        self.action_btn_layout.setContentsMargins(0, 0, 0, 0)
        self.action_btn_layout.setSpacing(8)

        # Copy Button (Ultra-Transparent Vector Icon - Zero Emojis / Zero Color)
        self.btn_copy = QPushButton("", self.action_btn_container)
        self.btn_copy.setObjectName("NotchCopyBtn")
        self.btn_copy.setToolTip("Copy response")
        self.btn_copy.setCursor(Qt.PointingHandCursor)
        self.btn_copy.setFixedSize(26, 26)
        if os.path.exists(_COPY_ICON):
            self.btn_copy.setIcon(QIcon(_COPY_ICON))
            self.btn_copy.setIconSize(QSize(13, 13))
        self.btn_copy.setStyleSheet("""
            QPushButton#NotchCopyBtn {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 13px;
                padding: 0px;
            }
            QPushButton#NotchCopyBtn:hover {
                background: rgba(255, 255, 255, 0.15);
                border-color: rgba(255, 255, 255, 0.25);
            }
        """)
        self.btn_copy.clicked.connect(self._on_copy_clicked)
        self.action_btn_layout.addWidget(self.btn_copy)

        # Voice Mute / Unmute Button (Ultra-Transparent Vector Icon - Zero Emojis / Zero Color)
        self.btn_voice = QPushButton("", self.action_btn_container)
        self.btn_voice.setObjectName("NotchVoiceBtn")
        self.btn_voice.setToolTip("Mute speech")
        self.btn_voice.setCursor(Qt.PointingHandCursor)
        self.btn_voice.setFixedSize(26, 26)
        if os.path.exists(_SPEAKER_ICON):
            self.btn_voice.setIcon(QIcon(_SPEAKER_ICON))
            self.btn_voice.setIconSize(QSize(13, 13))
        self.btn_voice.setStyleSheet("""
            QPushButton#NotchVoiceBtn {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 13px;
                padding: 0px;
            }
            QPushButton#NotchVoiceBtn:hover {
                background: rgba(255, 255, 255, 0.15);
                border-color: rgba(255, 255, 255, 0.25);
            }
        """)
        self.btn_voice.clicked.connect(self._on_voice_clicked)
        self.action_btn_layout.addWidget(self.btn_voice)

        self.action_btn_container.hide()
        self.footer_row.addWidget(self.action_btn_container)

        self.expanded_layout.addLayout(self.footer_row)

        # Dedicated Live Continuous Conversation Pill Button (Modeled after liquid glass pill in Image 2)
        self.live_btn_row = QHBoxLayout()
        self.live_btn_row.setContentsMargins(0, 2, 0, 2)
        self.live_btn_row.setAlignment(Qt.AlignCenter)

        self.btn_live = QPushButton("✦ Daemon Live", self.container)
        self.btn_live.setObjectName("NotchLiveBtn")
        self.btn_live.setCheckable(True)
        self.btn_live.setCursor(Qt.PointingHandCursor)
        self.btn_live.setFixedHeight(30)
        self.btn_live.setToolTip("Start / Stop continuous hands-free Daemon Live conversation")
        self.btn_live.setStyleSheet("""
            QPushButton#NotchLiveBtn {
                background: rgba(255, 255, 255, 0.08);
                color: #e2e8f0;
                border: 1px solid rgba(255, 255, 255, 0.18);
                border-radius: 15px;
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 0.02em;
                padding: 4px 18px;
            }
            QPushButton#NotchLiveBtn:hover {
                background: rgba(255, 255, 255, 0.16);
                border-color: rgba(255, 255, 255, 0.35);
                color: #ffffff;
            }
            QPushButton#NotchLiveBtn:checked {
                background: rgba(56, 189, 248, 0.22);
                color: #ffffff;
                border-color: rgba(56, 189, 248, 0.55);
            }
        """)
        self.btn_live.clicked.connect(self._on_live_clicked)
        self.live_btn_row.addWidget(self.btn_live)
        self.expanded_layout.addLayout(self.live_btn_row)

        # Waves Animation at the very bottom edge (Centered Siri Waveform strictly below copy & mute)
        self.waveform_row = QHBoxLayout()
        self.waveform_row.setContentsMargins(0, 3, 0, 1)
        self.waveform_row.setAlignment(Qt.AlignCenter)
        self.content_waveform = SiriWaveformWidget(self.container, height=18)
        self.content_waveform.setFixedWidth(280)
        self.waveform_row.addWidget(self.content_waveform, alignment=Qt.AlignCenter)
        self.expanded_layout.addLayout(self.waveform_row)

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

        # Start in rest mode (closed, without orbs) until activated by hotkey Ctrl+Alt
        self.close_to_rest(animated=False)

    def _get_active_screen_geometry(self) -> QRect:
        """Returns the geometry of the display containing the cursor or focus."""
        screen = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        return screen.availableGeometry() if screen else QRect(0, 0, 1920, 1080)

    def _reposition_collapsed(self, animated: bool = True):
        geom = self._get_active_screen_geometry()
        w = self._collapsed_w
        h = self._collapsed_h
        x = geom.x() + (geom.width() - w) // 2
        y = geom.y() + 4

        target_rect = QRect(x, y, w, h)
        if animated and self.isVisible():
            self.anim_geom.stop()
            self.anim_geom.setStartValue(self.geometry())
            self.anim_geom.setEndValue(target_rect)
            self.anim_geom.start()
        else:
            self.setGeometry(target_rect)

    def _calculate_needed_height(self, text: str) -> int:
        """Calculates dynamic required height to guarantee zero text clipping or truncation."""
        if not text:
            return self._normal_height
        text_w = 480
        fm = self.prompt_label.fontMetrics()
        bounding = fm.boundingRect(QRect(0, 0, text_w, 5000), Qt.TextWordWrap, text)
        text_h = bounding.height()
        # Overhead: main margins (14) + container margins (24) + header (34)
        # + footer row (30) + live button (34) + waveform row (24) + safety cushion (30) = 190px
        needed = text_h + 205
        return max(self._normal_height, min(620, needed))

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
        """User moved cursor away. Only schedule auto-close if no interactive card is active."""
        super().leaveEvent(event)
        if self._state == "IDLE" and not self._has_persistent_card():
            self._collapse_timer.start(1800)

    def _on_close_clicked(self):
        """User explicitly clicked ✕ close button: immediately halt speech, silence voice, and close notch."""
        try:
            from jarvis.voice.text_to_speech import tts_engine
            tts_engine.stop()
        except Exception:
            pass
        self.set_voice_active(False)
        self.close_requested.emit()
        self.close_to_rest(animated=True)

    def close_to_rest(self, animated: bool = True):
        """Smoothly closes the notch into rest mode without orbs and halts speech immediately."""
        self._collapse_timer.stop()
        try:
            from jarvis.voice.text_to_speech import tts_engine
            tts_engine.stop()
        except Exception:
            pass
        self.set_voice_active(False)
        self.set_state("REST")
        if animated and self.isVisible():
            geom = self.geometry()
            target_rect = QRect(geom.x(), geom.y(), geom.width(), 0)
            self.anim_geom.stop()
            try:
                self.anim_geom.finished.disconnect()
            except Exception:
                pass

            def _on_anim_done():
                self.disappear()
                try:
                    self.anim_geom.finished.disconnect(_on_anim_done)
                except Exception:
                    pass

            self.anim_geom.finished.connect(_on_anim_done)
            self.anim_geom.setStartValue(geom)
            self.anim_geom.setEndValue(target_rect)
            self.anim_geom.start()
        else:
            self.disappear()

    def collapse_to_pill(self, animated: bool = True):
        """Smoothly morphs from expanded HUD back into the minimalist curvy notch at the top."""
        self._collapse_timer.stop()
        try:
            from jarvis.voice.text_to_speech import tts_engine
            tts_engine.stop()
        except Exception:
            pass
        self.set_voice_active(False)
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
        if hasattr(self.container, "set_collapsed"):
            self.container.set_collapsed(True)
        self.container_layout.setContentsMargins(10, 2, 10, 2)
        self._reposition_collapsed(animated=animated)
        self.set_state("REST")
        self.show()
        self.raise_()

    def collapse(self):
        """Dismiss notch: close into rest mode without orbs and stop speech."""
        try:
            from jarvis.voice.text_to_speech import tts_engine
            tts_engine.stop()
        except Exception:
            pass
        self.set_voice_active(False)
        self.close_requested.emit()
        self.close_to_rest(animated=True)

    def disappear(self):
        """Completely hides the notch from screen in rest mode without orbs and stops all speech."""
        self._collapse_timer.stop()
        try:
            from jarvis.voice.text_to_speech import tts_engine
            tts_engine.stop()
        except Exception:
            pass
        self.set_voice_active(False)
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
        self.set_state("REST")

    def expand(self, target_h: Optional[int] = None):
        """Smoothly expands the notch downward into the liquid glass action panel."""
        self._collapse_timer.stop()
        self._is_collapsed = False
        self.collapsed_widget.hide()
        self.expanded_widget.show()
        if hasattr(self.container, "set_collapsed"):
            self.container.set_collapsed(False)
        self.container_layout.setContentsMargins(18, 10, 18, 14)

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
        y = geom.y() + 4
        target_rect = QRect(x, y, w, h)

        # If coming from hidden or tiny collapsed pill, start from pill geometry for authentic morphing
        current_geom = self.geometry()
        if not self.isVisible() or current_geom.height() <= 30 or current_geom.y() != y:
            start_rect = QRect(geom.x() + (geom.width() - self._collapsed_w) // 2, y, self._collapsed_w, self._collapsed_h)
            self.setGeometry(start_rect)
        else:
            start_rect = current_geom

        self.anim_geom.stop()
        try:
            self.anim_geom.finished.disconnect()
        except Exception:
            pass
        self.anim_geom.setStartValue(start_rect)
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

    def _on_orb_clicked(self):
        """Clicking the Gemini AI Liquid Orb toggles conversation / listening."""
        is_live = (self._state == "IDLE")
        self._on_live_clicked(is_live)
        self.clicked.emit()

    def _on_live_clicked(self, checked):
        if hasattr(self, "btn_live") and self.btn_live:
            self.btn_live.setChecked(checked)
            self.btn_live.setText("✦ Daemon Live Active • Tap to End" if checked else "✦ Daemon Live")
        if checked:
            self.header_title.setText("✦ Daemon Live")
            self.orb.set_state("LISTENING")
            if hasattr(self, "content_waveform") and self.content_waveform:
                self.content_waveform.set_state("LISTENING")
            if hasattr(self, "activity_dot") and self.activity_dot:
                self.activity_dot.setStyleSheet("background: #38bdf8; border-radius: 2.5px;")
        else:
            self.header_title.setText("✦ Ready")
            self.orb.set_state("IDLE")
            if hasattr(self, "content_waveform") and self.content_waveform:
                self.content_waveform.set_state("IDLE")
            if hasattr(self, "activity_dot") and self.activity_dot:
                self.activity_dot.setStyleSheet("background: rgba(255, 255, 255, 0.20); border-radius: 2.5px;")
        self.live_toggled.emit(checked)

    def update_energy(self, energy: float):
        if hasattr(self, "orb") and self.orb:
            self.orb.set_energy(energy)
        if hasattr(self, "content_waveform") and self.content_waveform:
            self.content_waveform.set_energy(energy)

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
            try:
                from jarvis.voice.text_to_speech import tts_engine
                tts_engine.stop()
            except Exception:
                pass
            self.set_voice_active(False)
            self.collapse()
            self.close_requested.emit()
        super().keyPressEvent(event)

    def closeEvent(self, event):
        try:
            from jarvis.voice.text_to_speech import tts_engine
            tts_engine.stop()
        except Exception:
            pass
        self.set_voice_active(False)
        super().closeEvent(event)

    def _on_copy_clicked(self):
        text = self.prompt_label.text().strip()
        if text and text not in ["What can I do for you?", "Ready • Hold Ctrl+Alt to speak", "Listening...", "Thinking..."]:
            from PySide6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            if clipboard:
                clipboard.setText(text)
            self.copy_clicked.emit(text)
            if os.path.exists(_CHECK_ICON):
                self.btn_copy.setIcon(QIcon(_CHECK_ICON))
                self.btn_copy.setText("")
            else:
                self.btn_copy.setText("✓")
            self.btn_copy.setStyleSheet("""
                QPushButton#NotchCopyBtn {
                    background: rgba(255, 255, 255, 0.18);
                    border: 1px solid rgba(255, 255, 255, 0.30);
                    border-radius: 13px;
                    padding: 0px;
                }
            """)
            QTimer.singleShot(1600, self._restore_copy_btn)

    def _restore_copy_btn(self):
        if os.path.exists(_COPY_ICON):
            self.btn_copy.setIcon(QIcon(_COPY_ICON))
            self.btn_copy.setText("")
        else:
            self.btn_copy.setText("📋")
        self.btn_copy.setStyleSheet("""
            QPushButton#NotchCopyBtn {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 13px;
                padding: 0px;
            }
            QPushButton#NotchCopyBtn:hover {
                background: rgba(255, 255, 255, 0.15);
                border-color: rgba(255, 255, 255, 0.25);
            }
        """)

    def _on_voice_clicked(self):
        mute = self._voice_active
        self.set_voice_active(not mute)
        self.voice_mute_toggled.emit(mute)

    def set_voice_active(self, is_active: bool):
        self._voice_active = is_active
        if is_active:
            if os.path.exists(_SPEAKER_ICON):
                self.btn_voice.setIcon(QIcon(_SPEAKER_ICON))
                self.btn_voice.setText("")
            else:
                self.btn_voice.setText("🔊")
            self.btn_voice.setToolTip("Mute speech")
            self.btn_voice.setStyleSheet("""
                QPushButton#NotchVoiceBtn {
                    background: rgba(255, 255, 255, 0.14);
                    border: 1px solid rgba(255, 255, 255, 0.25);
                    border-radius: 13px;
                    padding: 0px;
                }
                QPushButton#NotchVoiceBtn:hover {
                    background: rgba(255, 255, 255, 0.22);
                    border-color: rgba(255, 255, 255, 0.38);
                }
            """)
        else:
            if os.path.exists(_MUTE_ICON):
                self.btn_voice.setIcon(QIcon(_MUTE_ICON))
                self.btn_voice.setText("")
            else:
                self.btn_voice.setText("🔇")
            self.btn_voice.setToolTip("Read description aloud")
            self.btn_voice.setStyleSheet("""
                QPushButton#NotchVoiceBtn {
                    background: rgba(255, 255, 255, 0.05);
                    border: 1px solid rgba(255, 255, 255, 0.10);
                    border-radius: 13px;
                    padding: 0px;
                }
                QPushButton#NotchVoiceBtn:hover {
                    background: rgba(255, 255, 255, 0.15);
                    border-color: rgba(255, 255, 255, 0.25);
                }
            """)

    def set_state(self, state: str, text: str = ""):
        self._state = state
        self.orb.set_state(state)
        if hasattr(self, "content_waveform") and self.content_waveform:
            self.content_waveform.set_state(state)

        # Dynamic mic/system indicator dot on Dynamic Island capsule
        if hasattr(self, "activity_dot") and self.activity_dot:
            if state == "LISTENING":
                self.activity_dot.setStyleSheet("background: #34C759; border-radius: 2.5px;")  # Apple mic green
            elif state == "SPEAKING":
                self.activity_dot.setStyleSheet("background: #00E5FF; border-radius: 2.5px;")  # Siri blue/cyan
            elif state == "THINKING":
                self.activity_dot.setStyleSheet("background: #FF9F0A; border-radius: 2.5px;")  # Amber
            else:
                self.activity_dot.setStyleSheet("background: rgba(255, 255, 255, 0.22); border-radius: 2.5px;")

        if state == "REST":
            self.action_btn_container.hide()
            self.status_pill.hide()
            self._collapse_timer.stop()
            return

        if state == "IDLE":
            self.header_title.setText("✦ Ready")
            self.set_voice_active(False)
            # If an interactive card is open (job card, prompt card, email card), do NOT hide or auto-collapse!
            if self._has_persistent_card():
                self._collapse_timer.stop()
                return

            self.prompt_label.setText(text if text else "What can I do for you?")
            self.status_pill.setText("✦ Ready • Hold Ctrl+Alt to speak")
            self.status_pill.show()
            self.scroll_area.show()
            if text and text not in ["What can I do for you?", "Ready • Hold Ctrl+Alt to speak"]:
                self.action_btn_container.show()
                needed_h = self._calculate_needed_height(text)
                self.expand(needed_h)
                if not self.underMouse():
                    self._collapse_timer.start(2000)
            else:
                self.action_btn_container.hide()
                if not self.underMouse():
                    self._collapse_timer.start(1800)

        elif state == "LISTENING":
            self._collapse_timer.stop()
            self.set_voice_active(False)
            self.action_btn_container.hide()
            self.header_title.setText("✦ Listening...")
            self.prompt_label.setText(text or "Listening for your voice command...")
            self.status_pill.setText("✦ Listening • Release to execute")
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
            self.set_voice_active(False)
            self.action_btn_container.hide()
            self.header_title.setText("✦ Thinking...")
            self.prompt_label.setText(text or "Thinking...")
            self.status_pill.setText("✦ Processing...")
            self.status_pill.show()
            self.scroll_area.show()
            self.expand(self._normal_height)

        elif state == "EXECUTING":
            self._collapse_timer.stop()
            self.set_voice_active(False)
            self.header_title.setText("✦ Executing...")
            self.prompt_label.setText(text or "Performing action...")
            if self.pipeline_layout.count() > 0:
                self.status_pill.hide()
                self.pipeline_container.show()
            else:
                self.status_pill.setText("✦ Executing ✓")
                self.status_pill.show()
            self.scroll_area.show()
            self.expand(self._normal_height)

        elif state == "SPEAKING":
            self._collapse_timer.stop()
            self.set_voice_active(True)
            self.action_btn_container.show()
            self.header_title.setText("✦ Gemini")
            self.prompt_label.setText(text)
            self.status_pill.setText("✦ Speaking...")
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
            self.set_voice_active(False)
            self.action_btn_container.hide()
            self.header_title.setText("✦ Confirmation Required")
            self.prompt_label.setText(text or "Safety approval required")
            self.status_pill.setText("✦ Confirm Action")
            self.status_pill.show()
            self.expand(self._card_height)

        elif state == "ERROR":
            self.set_voice_active(False)
            self.action_btn_container.hide()
            self.header_title.setText("✕ Error")
            self.prompt_label.setText(text or "Operation failed")
            self.status_pill.setText("✕ Failed")
            self.status_pill.show()
            self.scroll_area.show()
            needed_h = self._calculate_needed_height(text)
            self.expand(needed_h)
            self._collapse_timer.start(4500)

    def show_action_preview(self, title: str, details: str, icon: str = "✦", requires_confirmation: bool = False):
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
        self.status_pill.setText(f"✦ {len(items)} items available")
        self.expand(self._folder_height)

    def show_prompt_card(self, topic: str, prompt_text: str):
        """Displays generated prompt with one-click copy button inside the notch."""
        self._collapse_timer.stop()
        self.scroll_area.hide()
        self.action_card.hide()
        self.folder_browser.hide()
        if hasattr(self, "email_list_card"):
            self.email_list_card.hide()
        self.header_title.setText(f"✦ Prompt: {topic.title()}")
        self.prompt_card.display_prompt(topic, prompt_text)
        self.prompt_card.show()
        self.status_pill.setText("✦ Click 'Copy Prompt' to copy")
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
        self.header_title.setText(f"✦ Gmail Inbox ({len(emails)})")
        self.email_list_card.display_emails(emails)
        self.email_list_card.show()
        self.status_pill.setText("✦ Recent Emails")
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
        self.header_title.setText(f"✦ {job_title}")
        self.job_card.display_job_application(data)
        self.job_card.show()
        match_pct = data.get("match_percentage", 96)
        self.status_pill.setText(f"✦ {match_pct}% Match • Ready")
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
        # Never close if user's cursor is hovering/pointing over the Dynamic Island!
        if self.underMouse():
            return
        # Never close if user is interacting with a card (Job, Prompt, Email, Folder)
        if self._has_persistent_card():
            return
        if self._state in ["IDLE", "SPEAKING", "ERROR"] and not self._is_collapsed:
            self.close_to_rest(animated=True)
