"""
JARVIS Intent & Command Router
Routes user voice transcripts to appropriate tools with dual-engine (offline first, cloud AI fallback).
"""

import webbrowser
from typing import Optional, Dict, Any, Tuple
from .intent import Intent, IntentCategory
from .local_engine import LocalSemanticEngine
from .provider import AIProvider
from .context import context_engine
from jarvis.tools import (
    WindowsTool,
    BrowserTool,
    FilesystemTool,
    DictationTool,
    KeyboardTool,
    ScreenTool,
    VisionTool,
    AIQueryTool,
    MessagingTool,
    MediaTool,
    ToolResult,
)
from jarvis.tools.memory_tool import MemoryTool
from jarvis.tools.calendar_tool import CalendarTool
from jarvis.tools.task_tool import TaskTool
from jarvis.app.config import config


class CommandRouter:
    def __init__(self):
        self.windows_tool = WindowsTool()
        self.browser_tool = BrowserTool()
        self.filesystem_tool = FilesystemTool()
        self.dictation_tool = DictationTool()
        self.keyboard_tool = KeyboardTool()
        self.screen_tool = ScreenTool()
        self.vision_tool = VisionTool()
        self.ai_query_tool = AIQueryTool()
        self.messaging_tool = MessagingTool()
        self.media_tool = MediaTool()

        self.ai_provider = AIProvider()
        self.memory_tool = MemoryTool()
        self.calendar_tool = CalendarTool()
        self.task_tool = TaskTool()

    def route_and_execute(self, transcript: str) -> Tuple[Intent, ToolResult]:
        """
        Parses intent and executes the corresponding tool action.
        Returns: (Intent, ToolResult)
        """
        active_mode = config.get("active_mode", "agent")

        # 1. Dictation Mode Bypass
        if active_mode == "dictation" and not transcript.lower().startswith("stop"):
            intent = Intent(category=IntentCategory.DICTATION, action="dictate", params={"text": transcript})
            res = self.dictation_tool.execute("dictate", text=transcript)
            return intent, res

        # 2. Local Semantic Engine (instant offline evaluation)
        intent = LocalSemanticEngine.parse(transcript)

        # 3. Cloud AI Provider Fallback
        if not intent:
            ctx = context_engine.get_desktop_context()
            intent = self.ai_provider.parse_intent(transcript, ctx)

        # 4. Fallback to General AI Query
        if not intent:
            intent = Intent(category=IntentCategory.AI_QUERY, action="query", params={"query": transcript})

        # Update context for follow-up conversational commands
        if intent.target:
            context_engine.update_interaction(intent.category.value, intent.target)

        # 5. Tool Execution
        result = self._dispatch_tool(intent)
        return intent, result

    def _dispatch_tool(self, intent: Intent) -> ToolResult:
        cat = intent.category

        if cat in [IntentCategory.APP_LAUNCH, IntentCategory.APP_CLOSE, IntentCategory.APP_FOCUS, IntentCategory.WINDOW_CONTROL, IntentCategory.SYSTEM_CONTROL]:
            return self.windows_tool.execute(intent.action, **intent.params)

        elif cat in [IntentCategory.WEB_NAVIGATION, IntentCategory.WEB_SEARCH, IntentCategory.BROWSER_ACTION]:
            return self.browser_tool.execute(intent.action, **intent.params)

        elif cat in [IntentCategory.FILE_SEARCH, IntentCategory.FILE_OPEN, IntentCategory.FILE_CREATE, IntentCategory.FILE_DELETE]:
            return self.filesystem_tool.execute(intent.action, **intent.params)

        elif cat == IntentCategory.DICTATION:
            return self.dictation_tool.execute("dictate", **intent.params)

        elif cat == IntentCategory.KEYBOARD_SHORTCUT:
            return self.keyboard_tool.execute(intent.action, **intent.params)

        elif cat == IntentCategory.MESSAGING:
            return self.messaging_tool.execute(intent.action, **intent.params)

        elif cat == IntentCategory.EMAIL:
            return self.messaging_tool.execute(intent.action, **intent.params)

        elif cat == IntentCategory.PHONE_CALL:
            return self.messaging_tool.execute(intent.action, **intent.params)

        elif cat == IntentCategory.MEDIA_CONTROL:
            return self.media_tool.execute(intent.action, **intent.params)

        elif cat == IntentCategory.MUSIC:
            # Play music: open search on YouTube/Spotify
            query = intent.params.get("query", "")
            if query:
                return self.browser_tool.execute("search_youtube", query=query)
            return ToolResult(status="FAILED", message="What would you like me to play?")

        elif cat == IntentCategory.SCREENSHOT:
            import pyautogui
            try:
                pyautogui.hotkey("win", "shift", "s")
                return ToolResult(status="SUCCESS", message="Screenshot tool opened. Select the area to capture.")
            except Exception as e:
                return ToolResult(status="FAILED", message=f"Screenshot failed: {e}")

        elif cat == IntentCategory.CLIPBOARD:
            return self.keyboard_tool.execute(intent.action, **intent.params)

        elif cat == IntentCategory.REMINDER:
            task = intent.params.get("task", "")
            amount = intent.params.get("amount", 5)
            unit = intent.params.get("unit", "minutes")
            return ToolResult(
                status="SUCCESS",
                message=f"I'll remind you to {task} in {amount} {unit}. Note: Desktop notifications for reminders are coming soon.",
            )

        elif cat == IntentCategory.SCREEN_ANALYSIS:
            # Capture screen then pass to vision
            cap_res = self.screen_tool.execute("capture_screen")
            img_path = cap_res.data.get("image_path", "")
            return self.vision_tool.execute("analyze", image_path=img_path, prompt=intent.params.get("prompt", ""))

        elif cat == IntentCategory.CURSOR_ANALYSIS:
            cap_res = self.screen_tool.execute("capture_cursor_region")
            img_path = cap_res.data.get("image_path", "")
            return self.vision_tool.execute("analyze", image_path=img_path, prompt=intent.params.get("prompt", ""))

        elif cat == IntentCategory.AI_QUERY:
            return self.ai_query_tool.execute(
                "query",
                query=intent.params.get("query", ""),
                answer=intent.confirmation_prompt,
            )

        elif cat == IntentCategory.CANCEL:
            return ToolResult(status="CANCELLED", message="Cancelled.")

        elif cat == IntentCategory.CALENDAR:
            return self.calendar_tool.execute(intent.action, **intent.params)

        elif cat == IntentCategory.TASK:
            return self.task_tool.execute(intent.action, **intent.params)

        elif cat == IntentCategory.MEMORY:
            return self.memory_tool.execute(intent.action, **intent.params)

        return ToolResult(status="FAILED", message="Unrecognized command category.")
