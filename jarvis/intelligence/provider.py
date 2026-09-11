"""
JARVIS Cloud AI Intelligence Provider
Connects to Groq / OpenAI LLM with robust JSON parsing, error resilience, and conversational reasoning.
"""

import re
import json
from typing import Optional, Dict, Any
from .intent import Intent, IntentCategory
from jarvis.app.config import config

SYSTEM_PROMPT = """You are JARVIS VoiceOS, an intelligent Windows voice assistant and operating system agent.
You speak in a warm, sophisticated, professional voice. Analyze the user's spoken command and output a single JSON object.

CRITICAL VOICE INSTRUCTIONS:
- 'spoken_response' MUST be 1 to 2 concise spoken sentences. It will be read aloud by text-to-speech.
- NEVER speak raw JSON, code, markdown symbols, asterisks, bullet points, software version numbers, or system schema keys.
- For conversational questions (AI_QUERY), provide a direct, insightful, and natural spoken answer.
- For OS actions (APP_LAUNCH, BROWSER_ACTION, etc.), provide a brief confirmation (e.g., "Opening YouTube for you.").

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
  "spoken_response": "Concise natural answer in 1 or 2 sentences"
}
"""


import urllib.request


class AIProvider:
    def __init__(self):
        self.gemini_key = config.get("gemini_api_key")
        self.groq_key = config.get("groq_api_key")
        self.provider = config.get("ai_provider", "gemini" if self.gemini_key else "groq")
        default_model = "gemini-3.6-flash" if self.provider == "gemini" else "openai/gpt-oss-120b"
        self.model = config.get("ai_model", default_model)

    def parse_intent(self, transcript: str, context: Optional[Dict[str, Any]] = None) -> Optional[Intent]:
        # Priority 1: Google Gemini if configured
        if self.gemini_key and (self.provider == "gemini" or not self.groq_key):
            intent = self._query_gemini(transcript, context)
            if intent:
                return intent

        # Priority 2: Groq
        if self.groq_key:
            intent = self._query_groq(transcript, context)
            if intent:
                return intent

        return None

    def _query_gemini(self, transcript: str, context: Optional[Dict[str, Any]] = None) -> Optional[Intent]:
        models_to_try = [self.model, "gemini-flash-latest", "gemini-3.6-flash"]
        seen = set()
        unique_models = []
        for m in models_to_try:
            if m and m not in seen and "gemini" in m:
                seen.add(m)
                unique_models.append(m)

        ctx_msg = ""
        if context:
            ctx_msg = f"\nForeground: '{context.get('window_title', '')}', Process: '{context.get('process_name', '')}'"

        payload = {
            "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
            "contents": [{"parts": [{"text": f"Spoken command: '{transcript}'{ctx_msg}"}]}],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.1,
                "maxOutputTokens": 1000,
            },
        }
        data_bytes = json.dumps(payload).encode("utf-8")

        for model in unique_models:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.gemini_key}"
                req = urllib.request.Request(
                    url,
                    data=data_bytes,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )

                with urllib.request.urlopen(req, timeout=10) as response:
                    res = json.loads(response.read().decode("utf-8"))
                    candidates = res.get("candidates", [])
                    if not candidates:
                        continue
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if not parts:
                        continue
                    raw_text = parts[0].get("text", "")
                    return self._parse_json_to_intent(raw_text, transcript)

            except Exception as e:
                print(f"[AIProvider] Gemini model {model} error: {e}")
                continue

        return None

    def _query_groq(self, transcript: str, context: Optional[Dict[str, Any]] = None) -> Optional[Intent]:
        try:
            from groq import Groq
            client = Groq(api_key=self.groq_key)

            ctx_msg = ""
            if context:
                ctx_msg = f"\nForeground: '{context.get('window_title', '')}', Process: '{context.get('process_name', '')}'"

            resp = client.chat.completions.create(
                model=self.model if "gemini" not in self.model else "openai/gpt-oss-120b",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Spoken command: '{transcript}'{ctx_msg}"},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=1000,
            )

            raw_text = resp.choices[0].message.content or ""
            return self._parse_json_to_intent(raw_text, transcript)

        except Exception as e:
            print(f"[AIProvider] Error querying Groq: {e}")
            return None

    def _parse_json_to_intent(self, raw_text: str, transcript: str) -> Intent:
        data = {}
        try:
            data = json.loads(raw_text)
        except Exception:
            json_match = re.search(r"(\{.*\})", raw_text, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group(1))
                except Exception:
                    pass

        if not data:
            return Intent(
                category=IntentCategory.AI_QUERY,
                action="query",
                params={"query": transcript},
                confirmation_prompt="I understood your command, but I need a moment to process it.",
            )

        category_str = data.get("category", "AI_QUERY")
        try:
            category = IntentCategory(category_str)
        except ValueError:
            category = IntentCategory.AI_QUERY

        spoken_resp = data.get("spoken_response", "").strip()
        if not spoken_resp:
            spoken_resp = f"Understood, executing {data.get('action', 'request')}."

        return Intent(
            category=category,
            target=data.get("target", ""),
            action=data.get("action", ""),
            params=data.get("params", {}),
            requires_confirmation=data.get("requires_confirmation", False),
            confirmation_prompt=spoken_resp,
        )
