"""
JARVIS VoiceOS Dynamic Notch HUD
Clean, glossy obsidian black top-center floating notch with pure white typography.
Guaranteed exact horizontal centering on active screen.
"""

from typing import Optional
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect, Signal, QPoint
from PySide6.QtWidgets import (
    QWidget,
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGraphicsDropShadowEffect,
)
from PySide6.QtGui import QColor, QMouseEvent, QGuiApplication, QCursor
from jarvis.ui.styles import NOTCH_BASE_STYLE, STATUS_CHIP_STYLE, STATUS_CHIP_DONE_STYLE
from jarvis.ui.orb import VoiceOSOrb
from jarvis.ui.action_card import ActionCard


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

        # Dimensions matching VoiceOS (Widened for pipeline steps)
        self._width = 520
        self._normal_height = 84
        self._card_height = 176

        # Layout Container - Modern VoiceOS Pill Capsule
        self.container = QFrame(self)
        self.container.setObjectName("NotchContainer")
        self.container.setStyleSheet(NOTCH_BASE_STYLE)

        # Deep Apple liquid glass ambient drop shadow beneath the notch
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(0, 0, 0, 200))
        shadow.setOffset(0, 6)
        self.container.setGraphicsEffect(shadow)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 12, 16, 20)
        main_layout.addWidget(self.container)

        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(14, 10, 16, 12)
        container_layout.setSpacing(8)

        # Top Content Row: Liquid Orb + (Prompt & Status Pill) + Close Button
        self.content_row = QHBoxLayout()
        self.content_row.setSpacing(14)
        self.content_row.setAlignment(Qt.AlignVCenter)

        # Glowing Neural Plasma Liquid Orb on the left (Clicking orb acts as action toggle)
        self.orb = VoiceOSOrb(self, size=52)
        self.orb.clicked.connect(self.clicked.emit)
        self.content_row.addWidget(self.orb, alignment=Qt.AlignVCenter)

        # Vertical text stack: prompt on top, status pill below
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        text_layout.setAlignment(Qt.AlignVCenter)

        self.prompt_label = QLabel("What can I do for you?")
        self.prompt_label.setObjectName("PromptLabel")
        self.prompt_label.setWordWrap(True)
        self.prompt_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        pill_layout = QHBoxLayout()
        pill_layout.setSpacing(8)

        self.status_pill = QLabel("⚡ Ready • Hold Ctrl+Alt to speak")
        self.status_pill.setObjectName("StatusPill")

        # Multi-step action pipeline container (VoiceOS chips)
        self.pipeline_container = QWidget()
        self.pipeline_layout = QHBoxLayout(self.pipeline_container)
        self.pipeline_layout.setContentsMargins(0, 0, 0, 0)
        self.pipeline_layout.setSpacing(6)
        self.pipeline_container.hide()

        pill_layout.addWidget(self.status_pill)
        pill_layout.addWidget(self.pipeline_container)
        pill_layout.addStretch()

        text_layout.addWidget(self.prompt_label)
        text_layout.addLayout(pill_layout)

        self.content_row.addLayout(text_layout)
        self.content_row.addStretch()

        # Close / Dismiss button (top right of the notch)
        self.btn_close = QPushButton("✕", self.container)
        self.btn_close.setObjectName("NotchCloseBtn")
        self.btn_close.setToolTip("Dismiss (Esc)")
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.setStyleSheet("""
            QPushButton#NotchCloseBtn {
                background: rgba(255, 255, 255, 12);
                color: rgba(255, 255, 255, 140);
                border: 1px solid rgba(255, 255, 255, 20);
                font-size: 11px;
                font-weight: bold;
                border-radius: 12px;
                min-width: 24px;
                max-width: 24px;
                min-height: 24px;
                max-height: 24px;
            }
            QPushButton#NotchCloseBtn:hover {
                background: rgba(255, 255, 255, 35);
                color: #ffffff;
                border-color: rgba(255, 255, 255, 60);
            }
        """)
        self.btn_close.clicked.connect(self.close_requested.emit)
        self.content_row.addWidget(self.btn_close, alignment=Qt.AlignVCenter)

        container_layout.addLayout(self.content_row)

        # Action Card for confirmation dialogues
        self.action_card = ActionCard(self)
        self.action_card.confirmed.connect(self.confirmed.emit)
        self.action_card.cancelled.connect(self.cancelled.emit)
        self.action_card.hide()
        container_layout.addWidget(self.action_card)

        # Setup animations
        self.anim_geom = QPropertyAnimation(self, b"geometry")
        self.anim_geom.setDuration(200)
        self.anim_geom.setEasingCurve(QEasingCurve.OutCubic)

        self.anim_opacity = QPropertyAnimation(self, b"windowOpacity")
        self.anim_opacity.setDuration(150)
        self.anim_opacity.setEasingCurve(QEasingCurve.OutCubic)

        self._is_fading_out = False
        self.reposition(self._width, self._normal_height, animated=False)

    def pop_up(self):
        """Shows the floating capsule HUD at top screen center."""
        self._is_fading_out = False
        self.anim_opacity.stop()
        self.setWindowOpacity(1.0)

        screen = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        geom = screen.availableGeometry() if screen else QRect(0, 0, 1920, 1080)

        self.container.adjustSize()
        hint = self.container.sizeHint()
        min_w = 460 if self.action_card.isVisible() else 320
        w = max(min_w, min(hint.width(), 620)) + 36
        h = max(self._normal_height, hint.height() + 32)
        x = geom.x() + (geom.width() - w) // 2
        target_y = geom.y() + 16

        self.setGeometry(x, target_y, w, h)
        self.show()
        self.raise_()
        self.activateWindow()

    def disappear(self):
        """Fades out smoothly and resets state."""
        if not self.isVisible() or self._is_fading_out:
            return

        self._is_fading_out = True
        self.anim_opacity.stop()

        def _finish_hide():
            if not self._is_fading_out:
                return
            self._is_fading_out = False
            self.hide()
            self.action_card.hide()
            self.clear_pipeline()
            self.setWindowOpacity(1.0)
            self.set_state("IDLE", "Ready • Hold Ctrl+Alt to speak")

        self.anim_opacity.setDuration(120)
        self.anim_opacity.setStartValue(self.windowOpacity())
        self.anim_opacity.setEndValue(0.0)
        self.anim_opacity.setEasingCurve(QEasingCurve.InCubic)
        try:
            self.anim_opacity.finished.disconnect()
        except Exception:
            pass
        self.anim_opacity.finished.connect(_finish_hide)
        self.anim_opacity.start()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            if self.action_card.isVisible() and self.action_card.geometry().contains(event.pos()):
                super().mousePressEvent(event)
                return
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close_requested.emit()
        super().keyPressEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        self.reposition(animated=False)

    def reposition(self, target_width: Optional[int] = None, target_height: Optional[int] = None, animated: bool = True):
        screen = QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()
        geom = screen.availableGeometry() if screen else QRect(0, 0, 1920, 1080)

        # Dynamic pill dimensions based on container content
        self.container.adjustSize()
        hint = self.container.sizeHint()
        min_w = 460 if self.action_card.isVisible() else 340
        if len(self.prompt_label.text()) > 60:
            min_w = max(min_w, 620)
        calc_w = max(min_w, min(hint.width(), 700))
        w = target_width or (calc_w + 36)
        
        calc_h = hint.height() + 32
        h = max(target_height or self._normal_height, calc_h)

        x = geom.x() + (geom.width() - w) // 2
        y = geom.y() + 16

        target_rect = QRect(x, y, w, h)

        if animated and self.isVisible():
            self.anim_geom.stop()
            self.anim_geom.setDuration(180)
            self.anim_geom.setStartValue(self.geometry())
            self.anim_geom.setEndValue(target_rect)
            self.anim_geom.setEasingCurve(QEasingCurve.OutCubic)
            self.anim_geom.start()
        else:
            self.setGeometry(target_rect)

    def set_state(self, state: str, text: str = ""):
        self._state = state
        self.orb.set_state(state)

        if state == "IDLE":
            if text and text != "Ready • Hold Ctrl+Alt to speak":
                self.prompt_label.setText(text)
            else:
                self.prompt_label.setText("What can I do for you?")
            self.status_pill.setText("⚡ Ready • Hold Ctrl+Alt to speak")
            self.status_pill.show()
            self.action_card.hide()
            self.clear_pipeline()
            self.reposition()

        elif state == "LISTENING":
            self.prompt_label.setText(text or "Listening...")
            self.status_pill.setText("🎙️ Listening • Release to execute")
            self.status_pill.show()
            self.action_card.hide()
            self.clear_pipeline()
            self.reposition()

        elif state == "PROCESSING":
            self.prompt_label.setText(text or "Thinking...")
            self.status_pill.setText("🔍 Processing...")
            self.status_pill.show()
            self.reposition()

        elif state == "EXECUTING":
            self.prompt_label.setText(text or "Performing action...")
            # Hide the generic status pill if we have pipeline steps showing
            if self.pipeline_layout.count() > 0:
                self.status_pill.hide()
                self.pipeline_container.show()
            else:
                self.status_pill.setText("⚡ Executing ✓")
                self.status_pill.show()
            self.reposition()

        elif state == "SPEAKING":
            self.prompt_label.setText(text)
            self.status_pill.setText("⚡ Speaking...")
            self.status_pill.show()
            self.action_card.hide()
            self.reposition()

        elif state == "CONFIRMATION_REQUIRED":
            self.prompt_label.setText(text or "Safety approval required")
            self.status_pill.setText("⚠️ Confirm Action")
            self.status_pill.show()
            self.action_card.show()
            self.reposition(target_height=self._card_height)

        elif state == "ERROR":
            self.prompt_label.setText(text or "Operation failed")
            self.status_pill.setText("✕ Failed")
            self.status_pill.show()
            self.clear_pipeline()
            self.reposition()

    def add_pipeline_step(self, label: str, icon: str, completed: bool = False, bg_color: tuple = (56, 189, 248)):
        """Adds a VoiceOS-style status chip to the action pipeline."""
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
        """Removes all action chips from the pipeline."""
        while self.pipeline_layout.count():
            item = self.pipeline_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.pipeline_container.hide()

    def show_action_preview(self, title: str, details: str, icon: str = "⚡", requires_confirmation: bool = False):
        self.action_card.update_card(title, details, icon, requires_confirmation)
        self.action_card.show()
        height = self._card_height if requires_confirmation else (self._card_height - 35)
        self.reposition(self._width, height)

    def update_energy(self, energy: float):
        self.orb.set_energy(energy)

    def set_mode(self, mode: str):
        pass
