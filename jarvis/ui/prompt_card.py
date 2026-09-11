"""
JARVIS Polished Prompt Card Widget
Renders generated prompts inside the VoiceOS notch with a prominent one-click copy button.
"""

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
)
import pyperclip


class PromptCardWidget(QFrame):
    copied = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.prompt_text = ""
        self.setObjectName("PromptCardWidget")
        self.setStyleSheet("""
            QFrame#PromptCardWidget {
                background: transparent;
                border: none;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Header: Topic badge + Copy button
        header_row = QHBoxLayout()
        header_row.setSpacing(8)

        self.title_lbl = QLabel("🪄 Polished Prompt")
        self.title_lbl.setStyleSheet("""
            color: #ffffff;
            font-size: 13.5px;
            font-weight: 700;
            background: transparent;
        """)
        header_row.addWidget(self.title_lbl)
        header_row.addStretch()

        self.copy_btn = QPushButton("📋 Copy Prompt")
        self.copy_btn.setCursor(Qt.PointingHandCursor)
        self.copy_btn.setStyleSheet("""
            QPushButton {
                background: #0A6CFF;
                color: #ffffff;
                border: none;
                border-radius: 12px;
                padding: 5px 14px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #257CFF;
            }
            QPushButton:pressed {
                background: #0056D2;
            }
        """)
        self.copy_btn.clicked.connect(self._on_copy_clicked)
        header_row.addWidget(self.copy_btn)

        layout.addLayout(header_row)

        # Prompt text area
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setFixedHeight(180)
        self.text_area.setStyleSheet("""
            QTextEdit {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.10);
                border-radius: 12px;
                color: rgba(255, 255, 255, 0.90);
                font-size: 13px;
                font-family: 'Segoe UI Variable Display', 'Segoe UI', sans-serif;
                line-height: 1.45;
                padding: 10px;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 6px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.15);
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.text_area)

    def display_prompt(self, topic: str, prompt_text: str):
        self.prompt_text = prompt_text
        self.title_lbl.setText(f"🪄 Prompt: {topic}")
        self.text_area.setPlainText(prompt_text)
        self.copy_btn.setText("📋 Copy Prompt")
        self.copy_btn.setStyleSheet("""
            QPushButton {
                background: #0A6CFF;
                color: #ffffff;
                border: none;
                border-radius: 12px;
                padding: 5px 14px;
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #257CFF;
            }
        """)

    set_prompt = display_prompt

    def _on_copy_clicked(self):
        if self.prompt_text:
            pyperclip.copy(self.prompt_text)
            self.copy_btn.setText("✓ Copied to Clipboard!")
            self.copy_btn.setStyleSheet("""
                QPushButton {
                    background: #10b981;
                    color: #ffffff;
                    border: none;
                    border-radius: 12px;
                    padding: 5px 14px;
                    font-size: 12px;
                    font-weight: 600;
                }
            """)
            self.copied.emit()
            QTimer.singleShot(2200, lambda: self.copy_btn.setText("📋 Copy Prompt"))
