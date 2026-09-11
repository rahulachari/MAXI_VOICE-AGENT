"""
JARVIS Action Preview Card
Renders a frosted glass preview card showing target action details with Confirm and Cancel controls.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
)
from jarvis.ui.styles import ACTION_CARD_STYLE


class ActionCard(QFrame):
    confirmed = Signal()
    cancelled = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ActionCard")
        self.setStyleSheet(ACTION_CARD_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 12)
        layout.setSpacing(6)

        # Header: Icon + Title
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        self.icon_label = QLabel("⚡")
        self.icon_label.setStyleSheet("font-size: 16px;")

        self.title_label = QLabel("Action Preview")
        self.title_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #f8fafc;")

        header_layout.addWidget(self.icon_label)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()

        # Details
        self.details_label = QLabel("")
        self.details_label.setWordWrap(True)
        self.details_label.setStyleSheet("font-size: 12px; color: #94a3b8; padding-left: 2px;")

        # Button row for confirmation
        self.button_container = QWidget()
        btn_layout = QHBoxLayout(self.button_container)
        btn_layout.setContentsMargins(0, 4, 0, 0)
        btn_layout.setSpacing(8)

        btn_layout.addStretch()

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setObjectName("CancelButton")
        self.btn_cancel.clicked.connect(self.cancelled.emit)

        self.btn_confirm = QPushButton("Confirm")
        self.btn_confirm.setObjectName("ConfirmButton")
        self.btn_confirm.clicked.connect(self.confirmed.emit)

        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_confirm)

        layout.addLayout(header_layout)
        layout.addWidget(self.details_label)
        layout.addWidget(self.button_container)

        self.button_container.hide()

    def update_card(self, title: str, details: str, icon: str = "⚡", requires_confirmation: bool = False):
        self.title_label.setText(title)
        self.details_label.setText(details)
        self.icon_label.setText(icon)

        if requires_confirmation:
            self.button_container.show()
        else:
            self.button_container.hide()
