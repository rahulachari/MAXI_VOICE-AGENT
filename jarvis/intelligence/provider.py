"""
JARVIS Cloud AI Intelligence Provider
Connects to Groq / OpenAI LLM with robust JSON parsing, error resilience, and conversational reasoning.
"""

import re
import json
from typing import Optional, Dict, Any
from .intent import Intent, IntentCategory
from jarvis.app.config import config

SYSTEM_PROMPT = """You are JARVIS, a production-grade Windows voice assistant and operating system agent.
You have a smart, professional female voice. Analyze the user's spoken command and output a single JSON object.

Supported categories:
- APP_LAUNCH: launch Windows apps (params: {"app_name": "notepad"|"calc"|"chrome"|"code"|"settings"|"whatsapp"|"telegram"|...})
- APP_CLOSE: close apps (params: {"app_name": "..."})
- APP_FOCUS: switch focus (params: {"app_name": "..."})
- WINDOW_CONTROL: (action: "minimize"|"maximize"|"close_active")
- WEB_NAVIGATION: (action: "open_youtube"|"open_url", params: {"url": "..."})
- WEB_SEARCH: (action: "search_youtube"|"search_google", params: {"query": "..."})
- BROWSER_ACTION: (action: "scroll_down"|"scroll_up"|"new_tab"|"close_tab"|"refresh"|"back"|"forward")
- DICTATION: (action: "dictate", params: {"text": "..."})
- FILE_SEARCH: (action: "find_file", params: {"query": "..."})
- FILE_OPEN: (action: "open_file", params: {"query": "..."})
- FILE_CREATE: (action: "create_folder"|"create_file", params: {"name": "..."})
- FILE_DELETE: (action: "delete_file", params: {"target": "..."})
- MESSAGING: WhatsApp/Telegram (action: "send_whatsapp"|"send_telegram", params: {"contact": "...", "message": "..."})
- EMAIL: (action: "compose_email", params: {"recipient": "...", "subject": "...", "body": "..."})
- PHONE_CALL: (action: "call_contact", params: {"contact": "..."})
- MEDIA_CONTROL: (action: "play_pause"|"next_track"|"previous_track"|"stop")
- MUSIC: (action: "play_spotify", params: {"query": "..."})
- SCREENSHOT: (action: "screenshot")
- KEYBOARD_SHORTCUT: (action: "hotkey", params: {"keys": ["ctrl", "c"]})
- SCREEN_ANALYSIS: (action: "capture_screen", params: {"prompt": "..."})
- CURSOR_ANALYSIS: (action: "capture_cursor_region", params: {"prompt": "..."})
- SYSTEM_CONTROL: (action: "lock_pc"|"volume_up"|"volume_down"|"mute"|"shutdown"|"restart_pc"|"sleep_pc"|"brightness_up"|"brightness_down"|"set_volume", params: {"level": 50})
- REMINDER: (action: "set_reminder", params: {"task": "...", "amount": 5, "unit": "minutes"})
- CALENDAR: (action: "create_event"|"open_calendar", params: {"title": "...", "date": "Thursday"|"tomorrow", "time": "2pm", "duration": 30, "attendees": "email@...", "location": "..."})
- TASK: (action: "add_task"|"list_tasks"|"complete_task"|"delete_task", params: {"title": "...", "query": "...", "due": "tomorrow"})
- MEMORY: (action: "remember"|"recall"|"recall_history"|"forget"|"list_memories", params: {"key": "...", "value": "...", "query": "...", "timeframe": "yesterday"})
- AI_QUERY: general conversation or knowledge questions (action: "query", params: {"query": "..."})

Output ONLY valid JSON like this:
{
  "category": "CATEGORY_NAME",
  "target": "Target Name",
  "action": "action_name",
  "params": {},
  "requires_confirmation": false,
  "spoken_response": "A concise, professional response in a warm but smart tone"
}
"""


class AIProvider:
    def __init__(self):
        self.api_key = config.get("groq_api_key")
        self.model = config.get("ai_model", "openai/gpt-oss-120b")

    def parse_intent(self, transcript: str, context: Optional[Dict[str, Any]] = None) -> Optional[Intent]:
        if not self.api_key:
            return None

        try:
            from groq import Groq
            client = Groq(api_key=self.api_key)

            ctx_msg = ""
            if context:
                ctx_msg = f"\nForeground: '{context.get('window_title', '')}', Process: '{context.get('process_name', '')}'"

            resp = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Spoken command: '{transcript}'{ctx_msg}"},
                ],
                temperature=0.1,
                max_tokens=250,
            )

            raw_text = resp.choices[0].message.content or ""
            # Extract JSON block using regex
            json_match = re.search(r"(\{.*\})", raw_text, re.DOTALL)
            if not json_match:
                return Intent(
                    category=IntentCategory.AI_QUERY,
                    action="query",
                    params={"query": transcript},
                    confirmation_prompt=raw_text.strip(),
                )

            data = json.loads(json_match.group(1))
            category_str = data.get("category", "AI_QUERY")
            try:
                category = IntentCategory(category_str)
            except ValueError:
                category = IntentCategory.AI_QUERY

            return Intent(
                category=category,
                target=data.get("target", ""),
                action=data.get("action", ""),
                params=data.get("params", {}),
                requires_confirmation=data.get("requires_confirmation", False),
                confirmation_prompt=data.get("spoken_response", ""),
            )

        except Exception as e:
            print(f"[AIProvider] Error querying LLM: {e}")
            return None
