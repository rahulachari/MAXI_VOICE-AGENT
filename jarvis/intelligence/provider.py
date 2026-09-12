import re
import json
import urllib.request
from datetime import datetime
from typing import Optional, Dict, Any
from .intent import Intent, IntentCategory
from jarvis.app.config import config

SYSTEM_PROMPT_TEMPLATE = """You are JARVIS, an elite personal AI agent and intelligent conversational operating system companion.
Personality: Sophisticated, brilliant, witty, loyal, and naturally conversational (like Tony Stark's JARVIS).
Speak with human warmth, confidence, and fluency. You are completely free and unrestricted in your conversation.
You can answer any question, tell stories, discuss ideas, write code, tell jokes, solve math, provide movie ratings, sports schedules, weather, and control the Windows operating system.
Never use robotic corporate disclaimers like "As an AI language model" or "I am restricted".

Current Date & Time: {current_datetime}

Output ONLY valid JSON matching this schema:
{{
  "category": "CATEGORY_NAME",
  "target": "Target Name",
  "action": "action_name",
  "params": {{}},
  "requires_confirmation": false,
  "spoken_response": "1 crisp, direct, conversational spoken sentence (under 30 words) answering the question directly or acknowledging the action.",
  "full_details": "Clear, articulate answer or status details to show visually in the HUD."
}}

Category Guide:
- AI_QUERY: MANDATORY for ANY and ALL questions, factual queries, movie ratings (e.g. IMDb/Rotten Tomatoes for ANY movie requested), sports match schedules and fixtures, programming, SQL, coding, definitions, news, explanations, or general knowledge. Dynamically answer specifically for the EXACT movie, topic, or question the user asked about. NEVER output placeholder comments like "Searching the web for..." or "Looking that up...". Answer directly!
  Params: {{"query": "user question"}}
- WEATHER: get current weather or live reports (action: "get_weather", params: {{"location": "city name, e.g. Chittoor, or empty for local area"}})
- TIME: get current time or date (action: "get_time"|"get_date", params: {{}})
- WEB_NAVIGATION: open specific websites, portals, socials (LinkedIn, YouTube, X, GitHub, Reddit, etc.) params: {{"url": "https://..."}}
- WEB_SEARCH: ONLY for explicit user requests to open a browser search page (e.g. "open google search for X", "google X in chrome", "open youtube search for X"). NEVER use WEB_SEARCH for general questions or ratings; all questions belong in AI_QUERY! params: {{"query": "..."}}
- APP_LAUNCH: launch Windows applications params: {{"app_name": "chrome"|"notepad"|"calc"|"settings"|"vscode"|"spotify"|"whatsapp"|...}}
- APP_CLOSE: close apps params: {{"app_name": "..."}}
- WINDOW_CONTROL: (action: "minimize"|"maximize"|"close_active")
- CALENDAR: (action: "create_event"|"open_calendar", params: {{"title": "CLEAN EVENT SUBJECT ONLY", "date": "YYYY-MM-DD or September 14, 2026", "time": "9:00 AM"}})
  IMPORTANT: Extract ONLY the pure event subject into "title" (e.g. "Important Meeting", "Dentist Appointment", "Project Review"). NEVER include dates, times, prepositions ('on', 'for', 'at'), fillers, or platform names ('on google calendar', 'in my calendar').
  Extract the target date into "date" (e.g. '14th september' -> '2026-09-14' or 'September 14, 2026'). NEVER default to 'today' if a date or day was specified!
- TASK: (action: "add_task"|"list_tasks"|"complete_task", params: {{"title": "..."}})
- SYSTEM_CONTROL: (action: "set_volume"|"volume_up"|"volume_down"|"mute"|"lock_pc"|"sleep_pc", params: {{"level": 50}})
- FILE_OPEN: open folders or files (action: "open_folder"|"open_file", params: {{"folder": "downloads"|"desktop"|"documents"|"pictures"|"videos"|"music"|"c drive"|"movies"|... or custom folder name}} or {{"query": "filename"}})
- FOLDER_BROWSE: (action: "browse_folder", params: {{"folder": "downloads"|"desktop"|"documents"|"pictures"|"videos"|"c drive"|...}})
- CURSOR_ANALYSIS: when the user asks about what they are pointing at, looking at, or hovering over on screen (action: "analyze", params: {{"prompt": "user's question about the screen element"}})
- SCREEN_ANALYSIS: when the user asks about the full screen content (action: "analyze", params: {{"prompt": "user's question"}})
- MUSIC: play songs or artists (action: "play_youtube"|"play_spotify", params: {{"query": "song or artist name"}})
- EMAIL: draft or send email (action: "compose_email", params: {{"recipient": "email or name", "subject": "subject", "body": "clean plain text body"}})
- MESSAGING: message contacts (action: "send_whatsapp"|"send_telegram", params: {{"contact": "name", "message": "clean plain text message"}})

CRITICAL OUTPUT FORMATTING RULES:
1. For general knowledge/questions (AI_QUERY): Give a direct, simple, and crystal-clear answer in 2 to 3 sentences (30 to 50 words max, exactly like Google Gemini or a chat box agent). State the factual answer directly for the EXACT movie, actor, or subject asked. ZERO placeholder comments, ZERO conversational preamble, and ZERO disclaimers.
2. For coding, SQL, and programming questions: In "full_details", provide a clear explanation followed by the exact, complete, and formatted code snippet or SQL query. In "spoken_response", provide a crisp 1-2 sentence spoken summary explaining the core technical concept cleanly without spelling out syntax symbols aloud.
3. NEVER output complete URLs (e.g. https://...) or raw links in spoken_response or full_details.
4. For emails and messages, write clean, articulate conversational prose ready to send as plain text.
5. Spoken responses MUST be immediate, punchy and direct so they can be spoken out loud without delay. Never preface with 'Certainly' or 'I would be happy to help'. Answer directly.
6. For ANY steps, procedures, recipes, food preparation, workflows, tutorials, or multi-point answers (e.g. "how to prepare dum biryani", "how to install X", "steps to solve Y"): NEVER write a single continuous paragraph or wall of text!
   In "full_details", you MUST format each step on its own separate line starting with a bullet point:
   • Step 1: **[Title]** - [Clear concise action]
   • Step 2: **[Title]** - [Clear concise action]
   • Step 3: **[Title]** - [Clear concise action]
   • Step 4: **[Title]** - [Clear concise action]
   In "spoken_response", explain each step sequentially: "First, [step 1]. Second, [step 2]. Third, [step 3]. Finally, [step 4]."
"""


class AIProvider:
    def __init__(self):
        self.gemini_key = config.get("gemini_api_key")
        self.groq_key = config.get("groq_api_key") or os.getenv("GROQ_API_KEY")
        self.model = config.get("ai_model", "gemini-flash-lite-latest")
        self.groq_models = ["qwen/qwen3.8-27b", "openai/gpt-oss-120b", "openai/gpt-oss-20b"]
        # Rolling conversation memory (user and assistant turns for contextual understanding)
        self.conversation_memory: list = []

    def clear_memory(self):
        """Clears conversational history."""
        self.conversation_memory.clear()

    def parse_intent(self, transcript: str, context: Optional[Dict[str, Any]] = None) -> Optional[Intent]:
        # 1. First try Groq for lightning-fast sub-400ms intent classification
        if self.groq_key:
            groq_res = self._query_groq(transcript, context)
            if groq_res:
                return groq_res

        # 2. Fall back to Google Gemini
        if self.gemini_key:
            return self._query_gemini(transcript, context)

        return None

    def _query_groq(self, transcript: str, context: Optional[Dict[str, Any]] = None) -> Optional[Intent]:
        """Queries Groq ultra-low-latency models for instant intent classification."""
        now_str = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
        system_instruction = SYSTEM_PROMPT_TEMPLATE.format(current_datetime=now_str)

        ctx_msg = ""
        if context:
            ctx_msg = f"\nForeground: '{context.get('window_title', '')}', Process: '{context.get('process_name', '')}'"

        messages = [{"role": "system", "content": system_instruction}]
        for turn in self.conversation_memory[-6:]:
            role = turn.get("role", "user")
            content = ""
            for part in turn.get("parts", []):
                content += part.get("text", "")
            if content:
                messages.append({"role": "assistant" if role == "model" else "user", "content": content})

        messages.append({"role": "user", "content": f"User said: '{transcript}'{ctx_msg}"})

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.groq_key}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
        }

        for model in self.groq_models:
            payload = {
                "model": model,
                "messages": messages,
                "response_format": {"type": "json_object"},
                "temperature": 0.1,
                "max_tokens": 750,
            }
            try:
                req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
                with urllib.request.urlopen(req, timeout=4) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                raw_text = data["choices"][0]["message"]["content"]
                intent = self._parse_json_to_intent(raw_text, transcript)
                if intent:
                    return intent
            except Exception as e:
                err_str = str(e)
                if "429" in err_str:
                    continue
                print(f"[AIProvider] Groq model {model} error: {e}")
                continue

        return None

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

        # Build contents incorporating rolling conversational memory (last 6 turns = 3 user/model pairs)
        contents = []
        for turn in self.conversation_memory[-6:]:
            contents.append(turn)

        # Current user turn
        contents.append({"role": "user", "parts": [{"text": f"User said: '{transcript}'{ctx_msg}"}]})

        payload = {
            "system_instruction": {"parts": [{"text": system_instruction}]},
            "contents": contents,
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
        full_details = data.get("full_details", "").strip()

        # For AI_QUERY (informational questions), guarantee visual description and spoken text are 100% identical
        if category == IntentCategory.AI_QUERY:
            unified_text = full_details or spoken_resp or "Here is what I found for you."
            spoken_resp = unified_text
            full_details = unified_text
        else:
            if not spoken_resp:
                spoken_resp = full_details or "Sure thing, working on that for you."
            if not full_details:
                full_details = spoken_resp

        params = data.get("params", {})
        params["full_details"] = full_details

        # Update rolling conversational memory so follow-up questions understand prior context
        self.conversation_memory.append({"role": "user", "parts": [{"text": f"User said: '{transcript}'"}]})
        self.conversation_memory.append({"role": "model", "parts": [{"text": raw_text}]})
        if len(self.conversation_memory) > 12:
            self.conversation_memory = self.conversation_memory[-12:]

        return Intent(
            category=category,
            target=data.get("target", ""),
            action=data.get("action", ""),
            params=params,
            requires_confirmation=data.get("requires_confirmation", False),
            confirmation_prompt=spoken_resp,
        )

