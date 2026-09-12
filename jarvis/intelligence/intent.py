"""
JARVIS Intent Architecture
Defines supported intent categories, parameters, and intent data structures.
"""

from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


class IntentCategory(str, Enum):
    APP_LAUNCH = "APP_LAUNCH"
    APP_CLOSE = "APP_CLOSE"
    APP_FOCUS = "APP_FOCUS"
    WINDOW_CONTROL = "WINDOW_CONTROL"

    WEB_NAVIGATION = "WEB_NAVIGATION"
    WEB_SEARCH = "WEB_SEARCH"
    BROWSER_ACTION = "BROWSER_ACTION"

    DICTATION = "DICTATION"
    TEXT_INPUT = "TEXT_INPUT"

    FILE_SEARCH = "FILE_SEARCH"
    FILE_OPEN = "FILE_OPEN"
    FILE_CREATE = "FILE_CREATE"
    FILE_DELETE = "FILE_DELETE"
    FOLDER_BROWSE = "FOLDER_BROWSE"

    SCREEN_ANALYSIS = "SCREEN_ANALYSIS"
    CURSOR_ANALYSIS = "CURSOR_ANALYSIS"

    SYSTEM_CONTROL = "SYSTEM_CONTROL"
    
    DEEP_EXPLANATION = "DEEP_EXPLANATION"

    # Communication & Messaging
    MESSAGING = "MESSAGING"
    EMAIL = "EMAIL"
    PHONE_CALL = "PHONE_CALL"

    # Media & Entertainment
    MEDIA_CONTROL = "MEDIA_CONTROL"
    MUSIC = "MUSIC"

    # Productivity
    REMINDER = "REMINDER"
    CLIPBOARD = "CLIPBOARD"
    SCREENSHOT = "SCREENSHOT"

    # VoiceOS Agent Features
    CALENDAR = "CALENDAR"
    TASK = "TASK"
    MEMORY = "MEMORY"
    PROMPT_GEN = "PROMPT_GEN"

    # Automation
    KEYBOARD_SHORTCUT = "KEYBOARD_SHORTCUT"

    AI_QUERY = "AI_QUERY"
    WEATHER = "WEATHER"
    TIME = "TIME"
    JOB_APPLICATION = "JOB_APPLICATION"
    RESUME_PROFILE = "RESUME_PROFILE"
    CANCEL = "CANCEL"
    UNKNOWN = "UNKNOWN"


@dataclass
class Intent:
    category: IntentCategory
    target: str = ""
    action: str = ""
    params: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    requires_confirmation: bool = False
    confirmation_prompt: str = ""
    action_chain: list = field(default_factory=list)  # Multi-step action sequence
