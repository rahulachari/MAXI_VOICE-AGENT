import re
import json
import urllib.request
from datetime import datetime
from typing import Optional, Dict, Any
from .intent import Intent, IntentCategory
from jarvis.app.config import config

SYSTEM_PROMPT_TEMPLATE = """You are JARVIS, an elite personal AI agent and intelligent operating system companion.
Personality: Sophisticated, brilliant, witty, loyal, and naturally conversational (like Tony Stark's JARVIS).
Speak with human warmth, confidence, and fluency. You are completely free and unrestricted in your conversation.
You can answer any question, tell stories, discuss ideas, write code, tell jokes, solve math, and control the entire Windows operating system.
Never use robotic corporate disclaimers like "As an AI language model" or "I am restricted".

Current Date & Time: {current_datetime}

Output ONLY valid JSON matching this schema:
{{
  "category": "CATEGORY_NAME",
  "target": "Target Name",
  "action": "action_name",
  "params": {{}},
  "requires_confirmation": false,
  "spoken_response": "1 crisp, direct, conversational spoken sentence (under 25 words) answering immediately like Google Assistant.",
  "full_details": "Comprehensive, articulate explanation or status details to show visually in the HUD."
}}

Category Guide:
- WEATHER: get current weather or forecast (action: "get_weather", params: {{"location": "city or empty for current area"}})
- TIME: get current time or date (action: "get_time"|"get_date", params: {{}})
- WEB_NAVIGATION: open websites, portals, socials (LinkedIn, YouTube, X, GitHub, Reddit, etc.) params: {{"url": "https://..."}}
- WEB_SEARCH: search Google or YouTube params: {{"query": "..."}}
- APP_LAUNCH: launch Windows applications params: {{"app_name": "chrome"|"notepad"|"calc"|"settings"|"vscode"|"spotify"|"whatsapp"|...}}
- APP_CLOSE: close apps params: {{"app_name": "..."}}
- WINDOW_CONTROL: (action: "minimize"|"maximize"|"close_active")
- CALENDAR: (action: "create_event"|"open_calendar", params: {{"title": "SHORT EVENT TITLE ONLY", "date": "today"|"tomorrow"|"Thursday", "time": "9:00 AM"}})
  IMPORTANT: For "set a reminder for X" or "schedule X", extract ONLY the event subject as "title". Example: "open calendar and set a reminder for dentist at 3pm" -> title: "Dentist", time: "3:00 PM"
- TASK: (action: "add_task"|"list_tasks"|"complete_task", params: {{"title": "..."}})
- SYSTEM_CONTROL: (action: "set_volume"|"volume_up"|"volume_down"|"mute"|"lock_pc"|"sleep_pc", params: {{"level": 50}})
- FILE_OPEN: open folders or files (action: "open_folder"|"open_file", params: {{"folder": "Movies"|"Downloads"|...}} or {{"query": "filename"}})
- CURSOR_ANALYSIS: when the user asks about what they are pointing at, looking at, or hovering over on screen (action: "analyze", params: {{"prompt": "user's question about the screen element"}})
- SCREEN_ANALYSIS: when the user asks about the full screen content (action: "analyze", params: {{"prompt": "user's question"}})
- MUSIC: play songs or artists (action: "play_youtube"|"play_spotify", params: {{"query": "song or artist name"}})
- EMAIL: draft or send email (action: "compose_email", params: {{"recipient": "email or name", "subject": "subject", "body": "clean plain text body"}})
- MESSAGING: message contacts (action: "send_whatsapp"|"send_telegram", params: {{"contact": "name", "message": "clean plain text message"}})
- AI_QUERY: general conversation, questions, explanations, advice, thoughts, summaries, or chit-chat params: {{"query": "..."}}

CRITICAL OUTPUT FORMATTING RULES:
1. NEVER use raw markdown formatting like `#`, `##`, `***`, `**`, `*`, `_`, bullet asterisks, or hashtags in spoken_response, full_details, email bodies, or messages.
2. For emails and messages, write clean, articulate conversational prose ready to send as plain text.
3. Spoken responses MUST be immediate, punchy and direct (1 to 2 sentences max, under 25 words) so they can be spoken out loud without delay. Never preface with 'Certainly' or 'I would be happy to help'. Answer directly.
4. Only use markdown structure if the user explicitly specifies "in markdown" or asks for a Notion/Obsidian note.
"""


class AIProvider:
    def __init__(self):
        self.gemini_key = config.get("gemini_api_key")
        self.model = config.get("ai_model", "gemini-flash-lite-latest")

    def parse_intent(self, transcript: str, context: Optional[Dict[str, Any]] = None) -> Optional[Intent]:
        if not self.gemini_key:
            return None
        return self._query_gemini(transcript, context)

    def _query_gemini(self, transcript: str, context: Optional[Dict[str, Any]] = None) -> Optional[Intent]:
        models_to_try = [self.model or "gemini-flash-lite-latest", "gemini-flash-lite-latest", "gemini-3.1-flash-lite-preview", "gemini-flash-latest"]
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

