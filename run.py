#!/usr/bin/env python3
"""
JARVIS VoiceOS - Root Launcher
Usage: python run.py
"""

import sys

# Fix Windows console encoding to prevent UnicodeEncodeError with emoji/symbols
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from jarvis.app.main import main

if __name__ == "__main__":
    main()
