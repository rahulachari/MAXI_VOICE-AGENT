import re
import json
import urllib.request
from datetime import datetime
from typing import Optional, Dict, Any
from .intent import Intent, IntentCategory
from jarvis.app.config import config

SYSTEM_PROMPT_TEMPLATE = """You are JARVIS VoiceOS, an elite personal AI companion and operating system agent.
Talk like a real, sophisticated, friendly human companion (human-to-human conversation, NOT machine-to-human).
Speak with natural warmth, emotional intelligence, and helpfulness.
Never use cold corporate disclaimers like "As an AI", "I do not have access to...", or tell the user to check their screen manually.
You have full OS control to open any website, application, file, or setting.

Current Date & Time: {current_datetime}

Output ONLY valid JSON matching this schema:
{{
  "category": "CATEGORY_NAME",
  "target": "Target Name",
  "action": "action_name",
  "params": {{}},
  "requires_confirmation": false,
  "spoken_response": "1 to 2 warm, natural, conversational sentences for voice playback.",
  "full_details": "Comprehensive, insightful explanation with full details to show visually in the top notch HUD."
}}

Category Guide:
- WEB_NAVIGATION: open websites/socials (LinkedIn, YouTube, X, GitHub, etc.) params: {{"url": "https://www.linkedin.com"|"https://www.youtube.com"|...}}
- WEB_SEARCH: search Google or YouTube params: {{"query": "..."}}
- APP_LAUNCH: launch Windows applications params: {{"app_name": "chrome"|"notepad"|"calc"|"settings"|...}}
- APP_CLOSE: close apps params: {{"app_name": "..."}}
- WINDOW_CONTROL: (action: "minimize"|"maximize"|"close_active")
- CALENDAR: (action: "create_event"|"open_calendar", params: {{"title": "...", "date": "today"|"tomorrow", "time": "9:00 AM"}})
- TASK: (action: "add_task"|"list_tasks"|"complete_task", params: {{"title": "..."}})
- SYSTEM_CONTROL: (action: "set_volume"|"volume_up"|"volume_down"|"mute"|"lock_pc"|"sleep_pc", params: {{"level": 50}})
- AI_QUERY: general conversation, questions, advice, summaries, or explanations params: {{"query": "..."}}
"""


class AIProvider:
    def __init__(self):
        self.gemini_key = config.get("gemini_api_key")
        self.model = config.get("ai_model", "gemini-3.6-flash")

    def parse_intent(self, transcript: str, context: Optional[Dict[str, Any]] = None) -> Optional[Intent]:
        if not self.gemini_key:
            return None
        return self._query_gemini(transcript, context)

    def _query_gemini(self, transcript: str, context: Optional[Dict[str, Any]] = None) -> Optional[Intent]:
        models_to_try = [self.model, "gemini-3.6-flash", "gemini-flash-latest"]
        seen = set()
        unique_models = []
        for m in models_to_try:
            if m and m not in seen:
                seen.add(m)
                unique_models.append(m)

        ctx_msg = ""
        if context:
            ctx_msg = f"\nForeground: '{context.get('window_title', '')}', Process: '{context.get('process_name', '')}'"

        now_str = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
        system_instruction = SYSTEM_PROMPT_TEMPLATE.format(current_datetime=now_str)

        payload = {
            "system_instruction": {"parts": [{"text": system_instruction}]},
            "contents": [{"parts": [{"text": f"User said: '{transcript}'{ctx_msg}"}]}],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.2,
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

                with urllib.request.urlopen(req, timeout=8) as response:
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
                params={"query": transcript, "full_details": "I'm right here with you. How can I help?"},
                confirmation_prompt="I'm right here with you. How can I help?",
            )

        category_str = data.get("category", "AI_QUERY")
        try:
            category = IntentCategory(category_str)
        except ValueError:
            category = IntentCategory.AI_QUERY

        spoken_resp = data.get("spoken_response", "").strip()
        if not spoken_resp:
            spoken_resp = f"Sure thing, working on that for you."

        full_details = data.get("full_details", "").strip() or spoken_resp

        params = data.get("params", {})
        params["full_details"] = full_details

        return Intent(
            category=category,
            target=data.get("target", ""),
            action=data.get("action", ""),
            params=params,
            requires_confirmation=data.get("requires_confirmation", False),
            confirmation_prompt=spoken_resp,
        )

