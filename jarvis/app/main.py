"""
JARVIS Desktop Application Entrypoint
Initializes Qt GUI application, loads high-DPI glassmorphism styles, and enters event loop.
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from jarvis.app.lifecycle import LifecycleManager


def main():
    # Windows high-DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("JARVIS VoiceOS")
    app.setOrganizationName("JARVIS")

    # Crucial: Keep running in tray when HUD or sidebar is hidden
    app.setQuitOnLastWindowClosed(False)

    lifecycle = LifecycleManager()
    lifecycle.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
