"""
JARVIS VoiceOS Approval Card (Human-In-The-Loop)
Modern question & action confirmation card matching the ApprovalCard design:
Multi-step question navigation, rolling odometer step indicators, radio & check options,
custom write-in answer input, quiet 'Skip' and accent 'Continue ⏎' buttons,
and animated sent approval badges.
"""

from typing import List, Dict, Optional, Union
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QWidget,
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
)
from PySide6.QtGui import QCursor, QFont


class OptionRow(QPushButton):
    """Interactive radio / checkbox row with animated selection indicator."""
    def __init__(self, text: str, is_radio: bool = True, parent=None):
        super().__init__(parent)
        self.option_text = text
        self.is_radio = is_radio
        self._checked = False
        self.setCursor(Qt.PointingHandCursor)
        self.setCheckable(True)
        self._update_appearance()

    def set_selected(self, selected: bool):
        self._checked = selected
        self._update_appearance()

    def is_selected(self) -> bool:
        return self._checked

    def _update_appearance(self):
        icon_shape = "border-radius: 8px;" if self.is_radio else "border-radius: 4px;"
        if self._checked:
            indicator_html = f"<span style='color: #000000; font-weight: bold;'>{'●' if self.is_radio else '✓'}</span>"
            indicator_bg = "#ffffff"
            text_color = "#ffffff"
        else:
            indicator_html = ""
            indicator_bg = "rgba(255, 255, 255, 0.08)"
            text_color = "#94a3b8"

        self.setText(f"{'● ' if self._checked and self.is_radio else ('✓ ' if self._checked else '○ ')}{self.option_text}")
        self.setStyleSheet(f"""
            QPushButton {{
                background: {"rgba(255, 255, 255, 0.08)" if self._checked else "rgba(255, 255, 255, 0.03)"};
                color: {text_color};
                border: 1px solid {"rgba(255, 255, 255, 0.25)" if self._checked else "rgba(255, 255, 255, 0.06)"};
                border-radius: 8px;
                padding: 6px 12px;
                text-align: left;
                font-size: 12.5px;
                font-family: 'Segoe UI Variable Display', 'Segoe UI', sans-serif;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.10);
                color: #ffffff;
                border-color: rgba(255, 255, 255, 0.18);
            }}
        """)


class ActionCard(QFrame):
    """
    Human-in-the-loop Approval & Action Card.
    Provides backward compatibility with update_card() while supporting
    multi-step questions, choices, custom write-ins, and step progress.
    """
    confirmed = Signal()
    cancelled = Signal()
    answer_submitted = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ActionCard")
        self.setStyleSheet("""
            QFrame#ActionCard {
                background: rgba(18, 20, 26, 0.96);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-top: 1.5px solid rgba(255, 255, 255, 0.25);
                border-radius: 18px;
            }
        """)

        self._questions: List[Dict] = []
        self._current_index = 0
        self._answers: Dict[int, List[int]] = {}
        self._custom_text: Dict[int, str] = {}
        self._option_buttons: List[OptionRow] = []

        self._init_ui()

    def _init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(14, 12, 14, 12)
        self.layout.setSpacing(10)

        # ── Header: Icon + Title/Question + Dismiss ──
        header_row = QHBoxLayout()
        header_row.setSpacing(8)

        self.icon_label = QLabel("⚡")
        self.icon_label.setStyleSheet("font-size: 15px; color: #38bdf8;")

        self.title_label = QLabel("Action Approval")
        self.title_label.setWordWrap(True)
        self.title_label.setStyleSheet("""
            font-size: 13.5px;
            font-weight: 600;
            color: #f8fafc;
            font-family: 'Segoe UI Variable Display', 'Segoe UI', sans-serif;
        """)

        self.btn_dismiss = QPushButton("✕")
        self.btn_dismiss.setCursor(Qt.PointingHandCursor)
        self.btn_dismiss.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #64748b;
                border: none;
                font-size: 12px;
                padding: 2px 6px;
            }
            QPushButton:hover { color: #f8fafc; }
        """)
        self.btn_dismiss.clicked.connect(self.cancelled.emit)

        header_row.addWidget(self.icon_label)
        header_row.addWidget(self.title_label, 1)
        header_row.addWidget(self.btn_dismiss)
        self.layout.addLayout(header_row)

        # ── Details / Description Text ──
        self.details_label = QLabel()
        self.details_label.setWordWrap(True)
        self.details_label.setStyleSheet("font-size: 12px; color: #94a3b8; padding-left: 2px;")
        self.layout.addWidget(self.details_label)

        # ── Options Container ──
        self.options_container = QWidget()
        self.options_layout = QVBoxLayout(self.options_container)
        self.options_layout.setContentsMargins(0, 0, 0, 0)
        self.options_layout.setSpacing(6)
        self.layout.addWidget(self.options_container)

        # ── Custom Write-in Input ──
        self.custom_input = QLineEdit()
        self.custom_input.setPlaceholderText("Something else…")
        self.custom_input.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
                color: #ffffff;
                padding: 6px 10px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: rgba(255, 255, 255, 0.25);
                background: rgba(255, 255, 255, 0.07);
            }
        """)
        self.custom_input.returnPressed.connect(self._advance)
        self.custom_input.textChanged.connect(self._on_custom_changed)
        self.layout.addWidget(self.custom_input)
        self.custom_input.hide()

        # ── Status Banner (Sent confirmation) ──
        self.sent_banner = QLabel("✓ Answers sent")
        self.sent_banner.setStyleSheet("""
            background: rgba(34, 197, 94, 0.15);
            color: #4ade80;
            border: 1px solid rgba(34, 197, 94, 0.25);
            border-radius: 8px;
            padding: 6px 12px;
            font-size: 12px;
            font-weight: 500;
        """)
        self.layout.addWidget(self.sent_banner)
        self.sent_banner.hide()

        # ── Footer: Step Navigation + Actions ──
        self.footer = QWidget()
        footer_layout = QHBoxLayout(self.footer)
        footer_layout.setContentsMargins(0, 4, 0, 0)
        footer_layout.setSpacing(8)

        # Step nav (e.g. < 1 / 3 >)
        self.nav_widget = QWidget()
        nav_layout = QHBoxLayout(self.nav_widget)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(4)

        self.btn_prev = QPushButton("‹")
        self.btn_prev.setCursor(Qt.PointingHandCursor)
        self.btn_prev.setStyleSheet("background: transparent; color: #64748b; font-size: 14px; border: none; padding: 0 4px;")
        self.btn_prev.clicked.connect(self._go_prev)

        self.step_label = QLabel("1 / 1")
        self.step_label.setStyleSheet("color: #64748b; font-size: 11.5px; font-weight: 600;")

        self.btn_next = QPushButton("›")
        self.btn_next.setCursor(Qt.PointingHandCursor)
        self.btn_next.setStyleSheet("background: transparent; color: #64748b; font-size: 14px; border: none; padding: 0 4px;")
        self.btn_next.clicked.connect(self._go_next)

        nav_layout.addWidget(self.btn_prev)
        nav_layout.addWidget(self.step_label)
        nav_layout.addWidget(self.btn_next)
        footer_layout.addWidget(self.nav_widget)

        footer_layout.addStretch()

        # Buttons: Skip & Continue
        self.btn_skip = QPushButton("Skip")
        self.btn_skip.setObjectName("CancelButton")
        self.btn_skip.setCursor(Qt.PointingHandCursor)
        self.btn_skip.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.06);
                color: #cbd5e1;
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.12);
                color: #ffffff;
            }
        """)
        self.btn_skip.clicked.connect(self._on_skip)

        self.btn_continue = QPushButton("Confirm ⏎")
        self.btn_continue.setObjectName("ConfirmButton")
        self.btn_continue.setCursor(Qt.PointingHandCursor)
        self.btn_continue.setStyleSheet("""
            QPushButton {
                background: #ffffff;
                color: #0f172a;
                border: none;
                border-radius: 8px;
                padding: 6px 16px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #f1f5f9;
            }
            QPushButton:disabled {
                background: rgba(255, 255, 255, 0.20);
                color: rgba(0, 0, 0, 0.40);
            }
        """)
        self.btn_continue.clicked.connect(self._advance)

        footer_layout.addWidget(self.btn_skip)
        footer_layout.addWidget(self.btn_continue)
        self.layout.addWidget(self.footer)

    def update_card(self, title: str, details: str, icon: str = "⚡", requires_confirmation: bool = False):
        """Standard action confirmation update (legacy support)."""
        self.title_label.setText(title)
        self.details_label.setText(details)
        self.icon_label.setText(icon)
        self.sent_banner.hide()
        self.custom_input.hide()
        self.nav_widget.hide()
        self._clear_options()

        if requires_confirmation:
            self.footer.show()
            self.btn_continue.setText("Confirm ⏎")
            self.btn_skip.setText("Cancel")
        else:
            self.footer.hide()

    def set_questions(self, questions: List[Dict]):
        """Sets up a multi-step human-in-the-loop approval questionnaire."""
        self._questions = questions
        self._current_index = 0
        self._answers = {}
        self._custom_text = {}
        self.sent_banner.hide()
        self.footer.show()
        self._render_current_question()

    def _render_current_question(self):
        if not self._questions:
            return

        q = self._questions[self._current_index]
        self.title_label.setText(q.get("q", "Select an option:"))
        self.details_label.setText(q.get("sub", ""))
        self.icon_label.setText(q.get("icon", "❓"))

        # Step nav
        self.nav_widget.show()
        self.step_label.setText(f"{self._current_index + 1} / {len(self._questions)}")
        self.btn_prev.setEnabled(self._current_index > 0)
        self.btn_next.setEnabled(self._current_index < len(self._questions) - 1)

        is_last = self._current_index == len(self._questions) - 1
        self.btn_continue.setText("Send ⏎" if is_last else "Continue ⏎")
        self.btn_skip.setText("Skip")

        # Options
        self._clear_options()
        opts = q.get("options", [])
        q_type = q.get("type", "radio")
        is_radio = q_type == "radio"
        picked = self._answers.get(self._current_index, [])

        for i, opt in enumerate(opts):
            btn = OptionRow(opt, is_radio=is_radio)
            btn.set_selected(i in picked)
            btn.clicked.connect(lambda checked=False, idx=i: self._on_option_toggled(idx))
            self.options_layout.addWidget(btn)
            self._option_buttons.append(btn)

        # Custom text
        self.custom_input.setText(self._custom_text.get(self._current_index, ""))
        self.custom_input.show()

        self._update_continue_enabled()

    def _on_option_toggled(self, idx: int):
        q = self._questions[self._current_index]
        is_radio = q.get("type", "radio") == "radio"

        if is_radio:
            self._answers[self._current_index] = [idx]
            for i, btn in enumerate(self._option_buttons):
                btn.set_selected(i == idx)
            # Auto-advance for single-choice radio after 350ms
            QTimer.singleShot(350, self._advance)
        else:
            picked = self._answers.get(self._current_index, [])
            if idx in picked:
                picked.remove(idx)
            else:
                picked.append(idx)
            self._answers[self._current_index] = picked
            for i, btn in enumerate(self._option_buttons):
                btn.set_selected(i in picked)

        self._update_continue_enabled()

    def _on_custom_changed(self, text: str):
        self._custom_text[self._current_index] = text
        self._update_continue_enabled()

    def _update_continue_enabled(self):
        has_choice = bool(self._answers.get(self._current_index)) or bool(self._custom_text.get(self._current_index, "").strip())
        self.btn_continue.setEnabled(has_choice)

    def _go_prev(self):
        if self._current_index > 0:
            self._current_index -= 1
            self._render_current_question()

    def _go_next(self):
        if self._current_index < len(self._questions) - 1:
            self._current_index += 1
            self._render_current_question()

    def _on_skip(self):
        if self._current_index < len(self._questions) - 1:
            self._go_next()
        else:
            self.cancelled.emit()

    def _advance(self):
        if not self._questions:
            self.confirmed.emit()
            return

        is_last = self._current_index == len(self._questions) - 1
        if is_last:
            self._finish_questions()
        else:
            self._go_next()

    def _finish_questions(self):
        self.sent_banner.show()
        self.footer.hide()
        self.options_container.hide()
        self.custom_input.hide()
        self.confirmed.emit()
        self.answer_submitted.emit({
            "answers": self._answers,
            "custom": self._custom_text,
        })

    def _clear_options(self):
        while self.options_layout.count():
            item = self.options_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._option_buttons.clear()
