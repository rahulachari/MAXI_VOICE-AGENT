"""
JARVIS Email List Card Widget
Renders inbox emails inside the VoiceOS notch with sender pills, subjects, and direct open button.
"""

import webbrowser
from typing import List, Dict, Any
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QWidget,
)


class EmailListCardWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("EmailListCardWidget")
        self.setStyleSheet("""
            QFrame#EmailListCardWidget {
                background: transparent;
                border: none;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Header
        header_row = QHBoxLayout()
        header_row.setSpacing(8)

        self.title_lbl = QLabel("✉️ Gmail Inbox")
        self.title_lbl.setStyleSheet("""
            color: #ffffff;
            font-size: 13.5px;
            font-weight: 700;
            background: transparent;
        """)
        header_row.addWidget(self.title_lbl)
        header_row.addStretch()

        self.open_btn = QPushButton("Open Gmail ↗")
        self.open_btn.setCursor(Qt.PointingHandCursor)
        self.open_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.08);
                color: rgba(255, 255, 255, 0.85);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 12px;
                padding: 4px 12px;
                font-size: 11.5px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: rgba(10, 108, 255, 0.35);
                color: #ffffff;
                border-color: #0A6CFF;
            }
        """)
        self.open_btn.clicked.connect(lambda: webbrowser.open("https://mail.google.com"))
        header_row.addWidget(self.open_btn)

        layout.addLayout(header_row)

        # Scroll area for email rows
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFixedHeight(200)
        self.scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
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

        self.list_container = QWidget()
        self.list_container.setStyleSheet("background: transparent;")
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 4, 0)
        self.list_layout.setSpacing(6)
        self.scroll.setWidget(self.list_container)

        layout.addWidget(self.scroll)

    def display_emails(self, emails: List[Dict[str, str]]):
        self.title_lbl.setText(f"✉️ Gmail Inbox ({len(emails)} messages)")

        # Clear existing
        while self.list_layout.count():
            child = self.list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not emails:
            empty_lbl = QLabel("No recent emails in inbox.")
            empty_lbl.setStyleSheet("color: rgba(255, 255, 255, 0.45); font-size: 13px; padding: 20px;")
            empty_lbl.setAlignment(Qt.AlignCenter)
            self.list_layout.addWidget(empty_lbl)
            return

        for em in emails:
            row = QFrame()
            row.setStyleSheet("""
                QFrame {
                    background: rgba(255, 255, 255, 0.04);
                    border: 1px solid rgba(255, 255, 255, 0.06);
                    border-radius: 10px;
                    padding: 4px;
                }
                QFrame:hover {
                    background: rgba(255, 255, 255, 0.08);
                }
            """)
            r_layout = QVBoxLayout(row)
            r_layout.setContentsMargins(8, 6, 8, 6)
            r_layout.setSpacing(3)

            top_line = QHBoxLayout()
            sender_pill = QLabel(em.get("sender", "Unknown"))
            sender_pill.setStyleSheet("""
                background: rgba(255, 255, 255, 0.10);
                color: #ffffff;
                border: 1px solid rgba(255, 255, 255, 0.14);
                border-radius: 10px;
                padding: 1px 8px;
                font-size: 12px;
                font-weight: 600;
            """)
            date_lbl = QLabel(em.get("date", ""))
            date_lbl.setStyleSheet("color: rgba(255, 255, 255, 0.38); font-size: 11px;")
            top_line.addWidget(sender_pill)
            top_line.addStretch()
            top_line.addWidget(date_lbl)
            r_layout.addLayout(top_line)

            subj_lbl = QLabel(em.get("subject", ""))
            subj_lbl.setWordWrap(True)
            subj_lbl.setStyleSheet("color: rgba(255, 255, 255, 0.88); font-size: 12.5px; padding-left: 2px;")
            r_layout.addWidget(subj_lbl)

            self.list_layout.addWidget(row)

        self.list_layout.addStretch()
