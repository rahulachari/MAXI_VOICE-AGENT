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
from jarvis.tools.weather_tool import WeatherTool
from jarvis.tools.email_reader_tool import EmailReaderTool
from jarvis.tools.prompt_gen_tool import PromptGeneratorTool
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
        self.weather_tool = WeatherTool()
        self.email_reader_tool = EmailReaderTool()
        self.prompt_gen_tool = PromptGeneratorTool()
        from jarvis.tools.job_application_tool import JobApplicationTool
        self.job_application_tool = JobApplicationTool()

    def route_and_execute(self, transcript: str, cursor_data: Optional[Dict[str, Any]] = None) -> Tuple[Intent, ToolResult]:
        """
        Parses intent and executes the corresponding tool action.
        Accepts optional in-memory cursor_data captured at hotkey press time.
        Returns: (Intent, ToolResult)
        """
        active_mode = config.get("active_mode", "agent")

        # 1. Dictation Mode Bypass
        if active_mode == "dictation" and not transcript.lower().startswith("stop"):
            intent = Intent(category=IntentCategory.DICTATION, action="dictate", params={"text": transcript})
            res = self.dictation_tool.execute("dictate", text=transcript)
            return intent, res

        # 0. Check for pending single clarifying question from previous turn
        pending = context_engine.get_pending_clarification()
        if pending:
            context_engine.clear_pending_clarification()
            missing_param = pending.get("missing_param")
            intent_dict = pending.get("intent_dict", {})
            params = intent_dict.get("params", {})
            params[missing_param] = transcript.strip()
            intent = Intent(
                category=IntentCategory(intent_dict["category"]),
                target=intent_dict.get("target"),
                action=intent_dict.get("action"),
                params=params,
                requires_confirmation=intent_dict.get("requires_confirmation", False),
            )
            result = self._dispatch_tool(intent, cursor_data=cursor_data)
            return intent, result

        # 1. Fast Local Semantic Engine (instant offline sub-millisecond recognition)
        intent = LocalSemanticEngine.parse(transcript)

        # 2. Cloud AI Provider for conversational reasoning and complex commands
        if not intent and self.ai_provider.gemini_key:
            ctx = context_engine.get_desktop_context()
            intent = self.ai_provider.parse_intent(transcript, ctx)

        # 3. Fallback: General AI Query
        if not intent:
            intent = Intent(
                category=IntentCategory.AI_QUERY,
                action="query",
                params={"query": transcript},
            )

        # 4. Action Registry Parameter Validation (single clarifying question if required param missing)
        from .action_registry import validate_intent_parameters
        clarify = validate_intent_parameters(intent)
        if clarify:
            missing_param, question = clarify
            context_engine.set_pending_clarification(
                {
                    "category": intent.category.value,
                    "target": intent.target,
                    "action": intent.action,
                    "params": intent.params,
                    "requires_confirmation": intent.requires_confirmation,
                },
                missing_param=missing_param,
                question=question,
            )
            return intent, ToolResult(
                status="NEEDS_CLARIFICATION",
                message=question,
                data={"clarifying_question": question, "missing_param": missing_param},
            )

        # Update context for follow-up conversational commands
        if intent.target:
            context_engine.update_interaction(intent.category.value, intent.target)

        # 5. Tool Execution
        result = self._dispatch_tool(intent, cursor_data=cursor_data)
        return intent, result

    def _dispatch_tool(self, intent: Intent, cursor_data: Optional[Dict[str, Any]] = None) -> ToolResult:
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

        elif cat == IntentCategory.EMAIL:
            if intent.action in ["read_emails", "check_emails", "check_gmail", "read_inbox", "read_gmail"]:
                return self.email_reader_tool.execute(intent.action, **intent.params)
            return self.messaging_tool.execute(intent.action, **intent.params)

        elif cat in [IntentCategory.MESSAGING, IntentCategory.PHONE_CALL]:
            return self.messaging_tool.execute(intent.action, **intent.params)

        elif cat == IntentCategory.PROMPT_GEN:
            return self.prompt_gen_tool.execute(intent.action, **intent.params)

        elif cat == IntentCategory.MEDIA_CONTROL:
            return self.media_tool.execute(intent.action, **intent.params)

        elif cat == IntentCategory.MUSIC:
            query = intent.params.get("query", "")
            target = (intent.target or "").lower()
            action = (intent.action or "").lower()
            if target == "spotify" or action == "play_spotify":
                return self.media_tool.execute("play_spotify", query=query)
            else:
                if query:
                    return self.browser_tool.execute("play_youtube", query=query)
                return self.media_tool.execute("play_pause")

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
            return self.task_tool.execute("add_task", title=task or f"Reminder ({amount} {unit})")

        elif cat == IntentCategory.SCREEN_ANALYSIS:
            cap_res = self.screen_tool.execute("capture_screen")
            img_bytes = cap_res.data.get("image_bytes") if cap_res.data else None
            return self.vision_tool.execute("analyze", image_bytes=img_bytes, prompt=intent.params.get("prompt", "Analyze what is on the screen."))

        elif cat == IntentCategory.CURSOR_ANALYSIS:
            # Use in-memory cursor capture from hotkey trigger if available
            if cursor_data and cursor_data.get("image_bytes"):
                img_bytes = cursor_data.get("image_bytes")
                text_hint = cursor_data.get("text_hint", "")
            else:
                cap_res = self.screen_tool.execute("capture_cursor_region")
                img_bytes = cap_res.data.get("image_bytes") if cap_res.data else None
                text_hint = cap_res.data.get("text_hint", "") if cap_res.data else ""

            action = intent.action or "analyze"
            prompt = intent.params.get("prompt", "What is at this cursor position and what does it show?")
            res = self.vision_tool.execute(action, image_bytes=img_bytes, text_hint=text_hint, prompt=prompt)
            if action == "find_linkedin" and res.requires_confirmation and res.data and "url" in res.data:
                # Morph the intent into open_url so confirming it just opens the browser without re-running vision
                intent.category = IntentCategory.WEB_NAVIGATION
                intent.target = "Browser"
                intent.action = "open_url"
                intent.params = {"url": res.data.get("url")}
            return res

        elif cat == IntentCategory.DEEP_EXPLANATION:
            return self.ai_query_tool.execute(
                "deep_explanation",
                topic=intent.params.get("topic", ""),
            )

        elif cat == IntentCategory.AI_QUERY:
            return self.ai_query_tool.execute(
                "query",
                query=intent.params.get("query", ""),
                answer=intent.confirmation_prompt,
                full_details=intent.params.get("full_details"),
            )

        elif cat == IntentCategory.WEATHER:
            action = intent.action or "get_weather"
            return self.weather_tool.execute(action, **intent.params)

        elif cat == IntentCategory.TIME:
            action = intent.action or "get_time"
            return self.weather_tool.execute(action, **intent.params)

        elif cat == IntentCategory.CANCEL:
            return ToolResult(status="CANCELLED", message="Cancelled.")

        elif cat == IntentCategory.CALENDAR:
            return self.calendar_tool.execute(intent.action, **intent.params)

        elif cat == IntentCategory.TASK:
            return self.task_tool.execute(intent.action, **intent.params)

        elif cat == IntentCategory.MEMORY:
            return self.memory_tool.execute(intent.action, **intent.params)

        elif cat == IntentCategory.FOLDER_BROWSE:
            from jarvis.tools.folder_registry import folder_registry
            action = intent.action or "browse_folder"
            if action == "set_alias":
                folder_src = intent.params.get("folder", "")
                alias_dst = intent.params.get("alias", "")
                path, err = folder_registry.resolve_folder(folder_src)
                if not path:
                    return ToolResult(status="FAILED", message=err or f"Could not find folder '{folder_src}'.")
                success = folder_registry.save_custom_alias(alias_dst, str(path))
                if success:
                    return ToolResult(status="SUCCESS", message=f"Saved alias: '{alias_dst}' now opens your {path.name} folder.")
                return ToolResult(status="FAILED", message=f"Could not save alias '{alias_dst}'.")

            folder_name = intent.params.get("folder", "downloads")
            path, err = folder_registry.resolve_folder(folder_name)
            if not path:
                return ToolResult(status="FAILED", message=err or f"Could not find folder '{folder_name}'.")

            # Validate security sandbox
            valid, err = folder_registry.validate_sandbox(path)
            if not valid:
                return ToolResult(status="FAILED", message=err)

            items = folder_registry.list_folder_contents(path, limit=15)
            # Open native Windows Explorer folder directly for user
            try:
                import os
                os.startfile(str(path))
            except Exception:
                pass

            summary_msg = f"Opened your {path.name.title()} folder."
            return ToolResult(
                status="SUCCESS",
                message=summary_msg,
                data={
                    "is_folder_browser": True,
                    "folder_name": path.name,
                    "folder_path": str(path),
                    "items": items,
                    "full_details": f"Folder: {path.name.title()} ({str(path)})\nItems: {len(items)} files listed.",
                },
            )

        elif cat == IntentCategory.JOB_APPLICATION:
            return self.job_application_tool.execute(intent.action, **intent.params)

        return ToolResult(status="FAILED", message="Unrecognized command category.")
