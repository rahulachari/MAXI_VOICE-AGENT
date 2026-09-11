"""
JARVIS Liquid Glass Folder Browser Widget
Renders a compact, scrollable file list preview inside the VoiceOS top-center notch panel.
Includes file open handlers, item icons, formatted sizes, and 'Reveal in Explorer/Finder'.
"""

import os
import sys
import subprocess
from typing import List, Dict, Any, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
)
from PySide6.QtGui import QCursor


class FileRowWidget(QFrame):
    """A clean, interactive row representing one file or subfolder."""
    clicked = Signal(str)

    def __init__(self, item: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.item_path = item.get("path", "")
        self.is_dir = item.get("is_dir", False)

        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 10px;
                padding: 4px 8px;
            }
            QFrame:hover {
                background: rgba(255, 255, 255, 0.10);
                border: 1px solid rgba(255, 255, 255, 0.14);
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(10)

        icon_lbl = QLabel(item.get("icon", "📄"))
        icon_lbl.setStyleSheet("font-size: 16px; background: transparent; border: none;")
        layout.addWidget(icon_lbl)

        name_lbl = QLabel(item.get("name", ""))
        name_lbl.setStyleSheet("""
            color: rgba(255, 255, 255, 0.92);
            font-size: 13px;
            font-weight: 500;
            background: transparent;
            border: none;
        """)
        layout.addWidget(name_lbl, 1)

        size_lbl = QLabel(item.get("size", ""))
        size_lbl.setStyleSheet("""
            color: rgba(255, 255, 255, 0.45);
            font-size: 11.5px;
            background: transparent;
            border: none;
        """)
        layout.addWidget(size_lbl)

        mod_lbl = QLabel(item.get("modified", ""))
        mod_lbl.setStyleSheet("""
            color: rgba(255, 255, 255, 0.38);
            font-size: 11px;
            background: transparent;
            border: none;
        """)
        layout.addWidget(mod_lbl)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.item_path)
        super().mousePressEvent(event)


class FolderBrowserWidget(QFrame):
    """
    Compact file browser panel embedded directly in the top-center VoiceOS notch.
    Zero floating windows. Opens native OS explorer only on explicit 'Reveal' request.
    """
    file_opened = Signal(str)
    reveal_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_folder_path = ""
        self.setObjectName("FolderBrowserWidget")
        self.setStyleSheet("""
            QFrame#FolderBrowserWidget {
                background: transparent;
                border: none;
            }
        """)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(8)

        # Header: folder title + count + "Reveal in Explorer" button
        self.header_row = QHBoxLayout()
        self.header_row.setSpacing(8)

        self.title_lbl = QLabel("📁 Folder Contents")
        self.title_lbl.setStyleSheet("""
            color: #ffffff;
            font-size: 13.5px;
            font-weight: 700;
            background: transparent;
        """)
        self.header_row.addWidget(self.title_lbl)
        self.header_row.addStretch()

        reveal_label = "Reveal in Finder" if sys.platform == "darwin" else "Reveal in Explorer"
        self.reveal_btn = QPushButton(f"↗ {reveal_label}")
        self.reveal_btn.setCursor(Qt.PointingHandCursor)
        self.reveal_btn.setStyleSheet("""
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
        self.reveal_btn.clicked.connect(self._on_reveal_clicked)
        self.header_row.addWidget(self.reveal_btn)

        self.main_layout.addLayout(self.header_row)

        # Scrollable items area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFixedHeight(210)
        self.scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 6px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.15);
                border-radius: 3px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.30);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        self.list_container = QWidget()
        self.list_container.setStyleSheet("background: transparent;")
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 6, 0)
        self.list_layout.setSpacing(6)
        self.scroll.setWidget(self.list_container)

        self.main_layout.addWidget(self.scroll)

    def display_folder(self, folder_name: str, folder_path: str, items: List[Dict[str, Any]]):
        """Populates the widget with resolved folder contents."""
        self.current_folder_path = folder_path
        self.title_lbl.setText(f"📁 {folder_name.title()} ({len(items)} items)")

        # Clear existing items
        while self.list_layout.count():
            child = self.list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not items:
            empty_lbl = QLabel("Folder is empty.")
            empty_lbl.setStyleSheet("color: rgba(255, 255, 255, 0.4); font-size: 13px; padding: 20px;")
            empty_lbl.setAlignment(Qt.AlignCenter)
            self.list_layout.addWidget(empty_lbl)
            return

        for item in items:
            row = FileRowWidget(item)
            row.clicked.connect(self._open_file_item)
            self.list_layout.addWidget(row)

        self.list_layout.addStretch()

    def _open_file_item(self, path: str):
        """Opens the selected file using the operating system's default handler."""
        if not path or not os.path.exists(path):
            return
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
            self.file_opened.emit(path)
        except Exception as e:
            print(f"[FolderBrowser] Error opening file {path}: {e}")

    def _on_reveal_clicked(self):
        """Opens the folder in the native OS file explorer as an explicit user escape hatch."""
        if not self.current_folder_path or not os.path.exists(self.current_folder_path):
            return
        try:
            if sys.platform == "win32":
                # Opens Explorer with folder opened
                subprocess.Popen(f'explorer.exe "{self.current_folder_path}"')
            elif sys.platform == "darwin":
                subprocess.Popen(["open", self.current_folder_path])
            else:
                subprocess.Popen(["xdg-open", self.current_folder_path])
            self.reveal_requested.emit(self.current_folder_path)
        except Exception as e:
            print(f"[FolderBrowser] Error revealing folder: {e}")
