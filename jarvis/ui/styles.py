"""
JARVIS VoiceOS Design System & Styling
Deep Black Obsidian Glassmorphism with Apple Liquid Glass Specular Aesthetics.
Status chips, app-specific badges, and VoiceOS-style typography.
"""

# Color Palette Tokens - MacBook Liquid Glass & OLED Black Aesthetic
COLOR_BACKGROUND_GLASS = "#000000"
COLOR_CARD_GLASS = "#05070d"

COLOR_TEXT_PRIMARY = "#f8fafc"
COLOR_TEXT_SECONDARY = "#94a3b8"
COLOR_TEXT_MUTED = "#64748b"

COLOR_BORDER_GLASS = "rgba(255, 255, 255, 0.12)"
COLOR_BORDER_RIM = "rgba(255, 255, 255, 0.24)"
COLOR_ACCENT_CYAN = "#38bdf8"
COLOR_ACCENT_BLUE = "#2563eb"
COLOR_ACCENT_METALLIC_DEEP = "#1e3a8a"

# VoiceOS Font Stack
FONT_STACK = "'Segoe UI Variable Display', 'Segoe UI', -apple-system, 'SF Pro Display', Roboto, sans-serif"
FONT_MONO = "'Cascadia Code', 'DM Mono', 'SF Mono', 'Consolas', monospace"

NOTCH_BASE_STYLE = f"""
QFrame#NotchContainer {{
    background: transparent;
    border: none;
}}

QLabel {{
    color: {COLOR_TEXT_PRIMARY};
    font-family: {FONT_STACK};
    background: transparent;
}}

QLabel#PromptLabel {{
    color: {COLOR_TEXT_PRIMARY};
    font-size: 14.5px;
    font-weight: 500;
    line-height: 1.5;
    letter-spacing: -0.1px;
    background: transparent;
}}

QLabel#StatusPill {{
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 9px;
    color: #cbd5e1;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.2px;
}}
QLabel#StatusPill:hover {{
    background: rgba(255, 255, 255, 0.12);
    border-color: rgba(255, 255, 255, 0.25);
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
    background: #000000;
    border: 1px solid #1c1c1e;
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

