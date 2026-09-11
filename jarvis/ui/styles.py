"""
JARVIS VoiceOS Design System & Styling
Deep Black Obsidian Glassmorphism with Apple Liquid Glass Specular Aesthetics.
Status chips, app-specific badges, and VoiceOS-style typography.
"""

# Color Palette Tokens - OLED Black Minimal WatchOS Style
COLOR_BACKGROUND_GLASS = "rgba(0, 0, 0, 0.95)"
COLOR_CARD_GLASS = "rgba(8, 8, 8, 0.98)"

COLOR_TEXT_PRIMARY = "#ffffff"
COLOR_TEXT_SECONDARY = "#a1a1aa"
COLOR_TEXT_MUTED = "#52525b"

COLOR_BORDER_GLASS = "rgba(255, 255, 255, 0.05)"
COLOR_BORDER_RIM = "rgba(255, 255, 255, 0.08)"
COLOR_ACCENT_CYAN = "#00f0ff"
COLOR_ACCENT_BLUE = "#38bdf8"

# VoiceOS Font Stack
FONT_STACK = "'Segoe UI Variable Display', 'Segoe UI', -apple-system, 'SF Pro Display', Roboto, sans-serif"
FONT_MONO = "'Cascadia Code', 'DM Mono', 'SF Mono', 'Consolas', monospace"

NOTCH_BASE_STYLE = f"""
QWidget#NotchContainer {{
    background: {COLOR_BACKGROUND_GLASS};
    border-left: 1px solid {COLOR_BORDER_GLASS};
    border-right: 1px solid {COLOR_BORDER_GLASS};
    border-bottom: 1.5px solid {COLOR_BORDER_RIM};
    border-top: none;
    border-top-left-radius: 0px;
    border-top-right-radius: 0px;
    border-bottom-left-radius: 24px;
    border-bottom-right-radius: 24px;
}}

QLabel {{
    color: {COLOR_TEXT_PRIMARY};
    font-family: {FONT_STACK};
}}

QLabel#PromptLabel {{
    color: {COLOR_TEXT_PRIMARY};
    font-size: 13.5px;
    font-weight: 600;
    letter-spacing: -0.15px;
}}

QLabel#StatusPill {{
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 11px;
    color: #a1a1aa;
    padding: 3px 12px;
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.15px;
}}
QLabel#StatusPill:hover {{
    background: rgba(255, 255, 255, 0.08);
    border-color: rgba(255, 255, 255, 0.15);
    color: #ffffff;
}}
"""

# Status chip styles for multi-step action pipeline
STATUS_CHIP_STYLE = """
QLabel#StatusChip {{
    background: rgba({bg_r}, {bg_g}, {bg_b}, 0.08);
    border: 1px solid rgba({bg_r}, {bg_g}, {bg_b}, 0.15);
    border-radius: 10px;
    color: rgba({bg_r}, {bg_g}, {bg_b}, 0.8);
    padding: 3px 10px;
    font-size: 10.5px;
    font-weight: 500;
    font-family: {font};
}}
"""

# Completed chip: muted with checkmark
STATUS_CHIP_DONE_STYLE = f"""
QLabel#StatusChipDone {{
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 10px;
    color: #52525b;
    padding: 3px 10px;
    font-size: 10.5px;
    font-weight: 500;
    font-family: {FONT_MONO};
}}
"""

ACTION_CARD_STYLE = f"""
QFrame#ActionCard {{
    background: {COLOR_CARD_GLASS};
    border: 1px solid rgba(255, 255, 255, 0.16);
    border-top: 1.5px solid rgba(255, 255, 255, 0.35);
    border-radius: 16px;
}}

QPushButton#ConfirmButton {{
    background: #ffffff;
    color: #000000;
    border: none;
    border-radius: 9px;
    padding: 7px 18px;
    font-weight: 700;
    font-size: 12px;
    font-family: {FONT_STACK};
}}
QPushButton#ConfirmButton:hover {{
    background: #f1f5f9;
}}

QPushButton#CancelButton {{
    background: rgba(255, 255, 255, 0.08);
    color: #e2e8f0;
    border: 1px solid rgba(255, 255, 255, 0.18);
    border-radius: 9px;
    padding: 7px 18px;
    font-size: 12px;
    font-weight: 500;
    font-family: {FONT_STACK};
}}
QPushButton#CancelButton:hover {{
    background: rgba(255, 255, 255, 0.16);
    color: #ffffff;
}}
"""

# Sidebar style is now defined in history_sidebar.py itself
SIDEBAR_STYLE = f"""
QWidget#SidebarContainer {{
    background: rgba(0, 0, 0, 0.98);
    border-right: 1px solid rgba(255, 255, 255, 0.05);
}}

QLineEdit#SearchInput {{
    background: rgba(255, 255, 255, 0.07);
    border: 1px solid rgba(255, 255, 255, 0.18);
    border-radius: 10px;
    color: #ffffff;
    padding: 8px 14px;
    font-size: 13px;
}}
QLineEdit#SearchInput:focus {{
    border: 1px solid rgba(255, 255, 255, 0.50);
    background: rgba(255, 255, 255, 0.12);
}}

QScrollArea {{
    border: none;
    background: transparent;
}}

QScrollBar:vertical {{
    border: none;
    background: transparent;
    width: 6px;
}}
QScrollBar::handle:vertical {{
    background: rgba(255, 255, 255, 0.22);
    border-radius: 3px;
}}
QScrollBar::handle:vertical:hover {{
    background: rgba(255, 255, 255, 0.45);
}}
"""

