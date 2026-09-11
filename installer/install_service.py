"""
JARVIS VoiceOS - Permanent Windows Installer Script
Sets up automatic startup with Windows, Start Menu shortcuts, and Desktop icons.
Uses pythonw.exe to run completely silently without any console window.
"""

import os
import sys
from pathlib import Path
import win32com.client
from PySide6.QtGui import QPixmap, QPainter, QColor, QRadialGradient, QBrush, QGuiApplication
from PySide6.QtCore import Qt, QRectF


def generate_app_icon(icon_path: Path):
    """Creates a high-resolution glowing VoiceOS celestial globe icon."""
    app = QGuiApplication.instance() or QGuiApplication(sys.argv)
    pix = QPixmap(128, 128)
    pix.fill(QColor(0, 0, 0, 0))

    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)

    # Atmosphere glow
    glow = QRadialGradient(64, 64, 60)
    glow.setColorAt(0.0, QColor(0, 200, 255, 140))
    glow.setColorAt(0.7, QColor(0, 100, 220, 40))
    glow.setColorAt(1.0, QColor(0, 0, 0, 0))
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(glow))
    p.drawEllipse(4, 4, 120, 120)

    # Globe core
    globe = QRadialGradient(50, 50, 55)
    globe.setColorAt(0.0, QColor(0, 230, 255))
    globe.setColorAt(0.4, QColor(0, 120, 230))
    globe.setColorAt(0.85, QColor(10, 30, 80))
    globe.setColorAt(1.0, QColor(5, 12, 35))
    p.setBrush(QBrush(globe))
    p.drawEllipse(18, 18, 92, 92)

    # Orbital arcs
    p.setPen(QColor(255, 255, 255, 90))
    p.drawEllipse(QRectF(38, 18, 52, 92))
    p.drawEllipse(QRectF(18, 42, 92, 44))

    p.end()
    icon_path.parent.mkdir(parents=True, exist_ok=True)
    pix.save(str(icon_path), "ICO")
    print(f"[Icon] Generated high-DPI icon at: {icon_path}")


def install():
    project_root = Path(__file__).resolve().parent.parent
    run_script = project_root / "run.py"
    icon_file = project_root / "installer" / "jarvis.ico"

    # Generate icon
    generate_app_icon(icon_file)

    # Determine pythonw executable
    python_dir = Path(sys.executable).parent
    pythonw_exe = python_dir / "pythonw.exe"
    if not pythonw_exe.exists():
        pythonw_exe = Path(sys.executable)

    shell = win32com.client.Dispatch("WScript.Shell")

    # Target locations
    appdata = Path(os.environ.get("APPDATA", ""))
    userprofile = Path(os.environ.get("USERPROFILE", ""))

    startup_dir = appdata / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    programs_dir = appdata / "Microsoft" / "Windows" / "Start Menu" / "Programs"
    desktop_dir = userprofile / "Desktop"

    shortcuts = [
        (startup_dir / "JARVIS VoiceOS.lnk", "Windows Startup (Auto-boot)"),
        (programs_dir / "JARVIS VoiceOS.lnk", "Start Menu"),
        (desktop_dir / "JARVIS VoiceOS.lnk", "Desktop"),
    ]

    print("\n" + "=" * 55)
    print("   JARVIS VoiceOS Permanent Installation")
    print("=" * 55)
    print(f"Target Script:     {run_script}")
    print(f"Silent Executable: {pythonw_exe}")
    print(f"App Icon:          {icon_file}\n")

    for shortcut_path, label in shortcuts:
        try:
            shortcut_path.parent.mkdir(parents=True, exist_ok=True)
            sc = shell.CreateShortCut(str(shortcut_path))
            sc.Targetpath = str(pythonw_exe)
            sc.Arguments = f'"{run_script}"'
            sc.WorkingDirectory = str(project_root)
            sc.WindowStyle = 7  # Minimized / Silent
            sc.Description = "JARVIS VoiceOS - AI Voice Assistant (Press Ctrl+Alt to speak)"
            if icon_file.exists():
                sc.IconLocation = f"{icon_file},0"
            sc.save()
            print(f"[OK] Installed to {label}:")
            print(f"     -> {shortcut_path}")
        except Exception as e:
            print(f"[Error] Failed to install {label}: {e}")

    print("\n" + "=" * 55)
    print("   Installation Complete!")
    print("   1. JARVIS will start automatically on Windows boot.")
    print("   2. You can also launch it from your Desktop or Start Menu.")
    print("   3. It runs quietly in the system tray. Press 'FN' anytime!")
    print("=" * 55 + "\n")


def uninstall():
    appdata = Path(os.environ.get("APPDATA", ""))
    userprofile = Path(os.environ.get("USERPROFILE", ""))

    targets = [
        appdata / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup" / "JARVIS VoiceOS.lnk",
        appdata / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "JARVIS VoiceOS.lnk",
        userprofile / "Desktop" / "JARVIS VoiceOS.lnk",
    ]

    print("\n" + "=" * 55)
    print("   JARVIS VoiceOS Uninstallation")
    print("=" * 55)
    for p in targets:
        if p.exists():
            try:
                p.unlink()
                print(f"[Removed] {p}")
            except Exception as e:
                print(f"[Error] Could not remove {p}: {e}")
        else:
            print(f"[Not Found] {p}")
    print("=" * 55 + "\n")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].lower() in ["uninstall", "--uninstall", "-u"]:
        uninstall()
    else:
        install()
