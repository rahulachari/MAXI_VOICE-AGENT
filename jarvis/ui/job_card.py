"""
JARVIS Autonomous Job Application Card Widget
Renders the job match analysis, matched projects, autofill data,
and one-click cover letter copy inside the VoiceOS Dynamic Island notch.
"""

from typing import Dict, Any
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QWidget,
)
import pyperclip


class JobCardWidget(QFrame):
    copied = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cover_letter_text = ""
        self.setObjectName("JobCardWidget")
        self.setStyleSheet("""
            QFrame#JobCardWidget {
                background: transparent;
                border: none;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Header Row: Job Title + Match Percentage Badge + Copy Button
        header_row = QHBoxLayout()
        header_row.setSpacing(8)

        self.title_lbl = QLabel("💼 Job Application")
        self.title_lbl.setStyleSheet("""
            color: #ffffff;
            font-size: 13.5px;
            font-weight: 700;
            background: transparent;
        """)
        header_row.addWidget(self.title_lbl)

        self.match_badge = QLabel("98% Match")
        self.match_badge.setStyleSheet("""
            background: rgba(16, 185, 129, 0.22);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.40);
            border-radius: 10px;
            padding: 2px 8px;
            font-size: 11px;
            font-weight: 700;
        """)
        header_row.addWidget(self.match_badge)
        header_row.addStretch()

        self.copy_btn = QPushButton("📋 Copy Letter")
        self.copy_btn.setCursor(Qt.PointingHandCursor)
        self.copy_btn.setStyleSheet("""
            QPushButton {
                background: #0A6CFF;
                color: #ffffff;
                border: none;
                border-radius: 12px;
                padding: 4px 12px;
                font-size: 11.5px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #1a78ff;
            }
        """)
        self.copy_btn.clicked.connect(self._copy_cover_letter)
        header_row.addWidget(self.copy_btn)

        layout.addLayout(header_row)

        # Scrollable container for job details, matched projects, and fields
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.2);
                border-radius: 2px;
            }
        """)

        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background: transparent;")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(10, 10, 10, 10)
        self.content_layout.setSpacing(6)

        # Company & Role
        self.company_role_lbl = QLabel()
        self.company_role_lbl.setStyleSheet("color: #e2e8f0; font-size: 13px; font-weight: 600;")
        self.company_role_lbl.setWordWrap(True)
        self.content_layout.addWidget(self.company_role_lbl)

        # Candidate Details Row
        self.candidate_lbl = QLabel()
        self.candidate_lbl.setStyleSheet("color: #94a3b8; font-size: 11.5px;")
        self.candidate_lbl.setWordWrap(True)
        self.content_layout.addWidget(self.candidate_lbl)

        # Matched Projects Header & List
        self.projects_lbl = QLabel()
        self.projects_lbl.setStyleSheet("color: #cbd5e1; font-size: 12px; line-height: 1.4;")
        self.projects_lbl.setWordWrap(True)
        self.content_layout.addWidget(self.projects_lbl)

        self.scroll_area.setWidget(self.content_widget)
        layout.addWidget(self.scroll_area)

    def display_job_application(self, data: Dict[str, Any]):
        job_title = data.get("job_title", "Software Engineer")
        company = data.get("company", "Company")
        match_pct = data.get("match_percentage", 96)
        fields = data.get("fields", {})
        top_projects = data.get("top_projects", [])
        self.cover_letter_text = data.get("cover_letter", "")

        self.title_lbl.setText(f"💼 {job_title}")
        self.match_badge.setText(f"{match_pct}% Match")
        self.company_role_lbl.setText(f"Applying to {company} as {job_title}")
        
        cand_name = fields.get("Full Name", "")
        cand_email = fields.get("Email Address", "")
        cand_phone = fields.get("Phone Number", "")
        cand_github = fields.get("GitHub Profile", "")
        self.candidate_lbl.setText(
            f"👤 {cand_name} • 📧 {cand_email} • 📱 {cand_phone}\n"
            f"🐙 GitHub: {cand_github}"
        )

        proj_items = []
        for p in top_projects[:2]:
            t = p.get("title", "")
            d = p.get("description", "")
            stack = ", ".join(p.get("tech_stack", []))
            proj_items.append(f"<b>• {t}</b>: {d}<br><span style='color: #38bdf8;'>Tech: {stack}</span>")

        if proj_items:
            self.projects_lbl.setText(
                "<span style='color: #60a5fa; font-weight: bold;'>🎯 Matched Proof Projects:</span><br>" +
                "<br>".join(proj_items)
            )
        else:
            self.projects_lbl.setText("<span style='color: #34d399;'>✓ Profile details ready to submit.</span>")

    def _copy_cover_letter(self):
        if self.cover_letter_text:
            pyperclip.copy(self.cover_letter_text)
            self.copy_btn.setText("✓ Copied!")
            self.copy_btn.setStyleSheet("""
                QPushButton {
                    background: #10B981;
                    color: #ffffff;
                    border: none;
                    border-radius: 12px;
                    padding: 4px 12px;
                    font-size: 11.5px;
                    font-weight: 600;
                }
            """)
            self.copied.emit()
            QTimer.singleShot(2500, self._reset_copy_btn)

    def _reset_copy_btn(self):
        self.copy_btn.setText("📋 Copy Letter")
        self.copy_btn.setStyleSheet("""
            QPushButton {
                background: #0A6CFF;
                color: #ffffff;
                border: none;
                border-radius: 12px;
                padding: 4px 12px;
                font-size: 11.5px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #1a78ff;
            }
        """)
