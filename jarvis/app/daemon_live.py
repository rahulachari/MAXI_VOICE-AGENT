"""
JARVIS Daemon Live Mode Session Manager
Continuous, autonomous hands-free multi-turn voice interaction engine.
Runs as a continuous conversational daemon with seamless speech-to-speech looping.
"""

import os
import threading
import json
import time
import urllib.request
import base64
from typing import Callable
from jarvis.app.config import config
from jarvis.tools.vision_tool import VisionTool
from jarvis.tools.screen_tool import ScreenTool
from jarvis.voice.text_to_speech import tts_engine
from jarvis.utils.text_cleaner import clean_spoken_text
from jarvis.utils.cursor_logger import log_layer


class DaemonLiveSessionManager:
    """Continuous conversational daemon session manager.
    Keeps listening hands-free, processes multi-turn conversations back-to-back,
    and loops seamlessly without dropping user speech."""

    def __init__(self, on_state_change: Callable[[str, str], None], start_listening_callback: Callable[[], None]):
        self.is_active = False
        self.history = []
        self.vision = VisionTool()
        self.screen_tool = ScreenTool()
        self.on_state_change = on_state_change
        self.start_listening = start_listening_callback
        self._turn_lock = threading.Lock()

    def toggle(self):
        if self.is_active:
            self.stop()
        else:
            self.start()

    def start(self):
        self.is_active = True
        self.history = []
        print("[DaemonLive] Starting continuous Daemon Live session.")
        self.on_state_change("LISTENING", "Daemon Live active • Speak naturally!")
        # Brief pause to ensure clean stream initialization
        threading.Timer(0.15, self._safe_start_listening).start()

    def stop(self):
        self.is_active = False
        print("[DaemonLive] Stopping Daemon Live session.")
        if tts_engine.is_speaking():
            tts_engine.stop()
        self.on_state_change("IDLE", "Ready • Hold Ctrl+Alt to speak")

    def _safe_start_listening(self):
        if self.is_active:
            try:
                self.start_listening()
            except Exception as e:
                print(f"[DaemonLive] Failed to start listening: {e}")

    def process_turn(self, transcript: str):
        if not self.is_active:
            return

        t_lower = transcript.strip().lower()
        # Handle voice exit commands
        if t_lower in ["exit", "stop", "quit", "close", "stop daemon", "exit daemon", "goodbye", "bye"]:
            print("[DaemonLive] Voice exit command received. Stopping session.")
            self.on_state_change("SPEAKING", "Ending Daemon Live session. Goodbye!")
            def _on_exit_done():
                self.stop()
            tts_engine.speak("Ending Daemon Live session. Goodbye!", on_finish=_on_exit_done)
            return

        self.on_state_change("PROCESSING", f"'{transcript}'")

        def _worker():
            with self._turn_lock:
                if not self.is_active:
                    return

                try:
                    # 1. Check if user query actually requires visual/screen context
                    t_low = transcript.lower()
                    is_visual = any(w in t_low for w in [
                        "this", "look at", "what is on", "screen", "what do you see", "read this", "pointing", "cursor", "what's this"
                    ])

                    cursor_bytes, text_hint = None, ""
                    if is_visual:
                        log_layer(3, "Capturing cursor ROI for visual Daemon Live query")
                        cursor_bytes, text_hint = self.screen_tool.capture_cursor_region_bytes(radius=280)

                    # 2. Build Gemini prompt
                    gemini_key = config.get("gemini_api_key")
                    if not gemini_key:
                        self.on_state_change("ERROR", "Gemini API Key missing for Daemon Live.")
                        self._resume_listening_after_delay(2.0)
                        return

                    contents = []
                    # Inject rolling history (last 6 turns for rapid, context-rich conversation)
                    for turn in self.history[-6:]:
                        contents.append(turn)

                    # Current user turn
                    prompt_content = f"User says: {transcript}"
                    if text_hint:
                        prompt_content += f"\n[Text at cursor: '{text_hint}']"

                    user_parts = [{"text": prompt_content}]

                    if cursor_bytes and len(cursor_bytes) > 200:
                        cursor_b64 = base64.b64encode(cursor_bytes).decode("utf-8")
                        user_parts.append({
                            "inlineData": {
                                "mimeType": "image/jpeg",
                                "data": cursor_b64
                            }
                        })

                    current_turn = {"role": "user", "parts": user_parts}
                    contents.append(current_turn)

                    sys_instruction = {
                        "parts": [{
                            "text": (
                                "You are JARVIS Daemon Live, a warm, witty, remarkably natural conversational partner. "
                                "You and the user are having a real-time, continuous hands-free dialogue. "
                                "RULES:\n"
                                "1. Talk like an articulate, empathetic, human friend. Never say 'How can I help', 'As an AI', or mission jargon.\n"
                                "2. Keep answers concise and snappy: 1 to 2 spoken sentences (under 30 words) so dialogue flows fast.\n"
                                "3. When the user asks 'what is this' or points at anything on screen, explain directly.\n"
                                "4. No markdown formatting, no asterisks, no bullets. Plain spoken conversation only.\n"
                                "5. For recipes or cooking: explain step by step in clear sequential order: 'Here is how to prepare it step by step. First, [step 1]. Second, [step 2]. Third, [step 3]. Finally, [step 4].' Never give a dense paragraph."
                            )
                        }]
                    }

                    max_toks = 300 if any(w in t_low for w in ["prepare", "cook", "recipe", "make", "biryani"]) else 100
                    answer_text = None
                    groq_key = config.get("groq_api_key") or os.getenv("GROQ_API_KEY")

                    # 1. Try Groq for non-visual turns (instant ~280ms inference)
                    if not is_visual and groq_key:
                        try:
                            groq_msgs = [
                                {
                                    "role": "system",
                                    "content": (
                                        "You are JARVIS Daemon Live, a warm, witty, remarkably natural conversational partner. "
                                        "You and the user are having a real-time, continuous hands-free dialogue. "
                                        "RULES:\n"
                                        "1. Talk like an articulate, empathetic, human friend. Never say 'How can I help', 'As an AI', or mission jargon.\n"
                                        "2. Keep answers concise and snappy: 1 to 2 spoken sentences (under 30 words) so dialogue flows fast.\n"
                                        "3. Plain spoken conversation only. No markdown formatting, no asterisks, no bullets.\n"
                                        "4. For recipes/steps: sequential spoken order: 'First, [step 1]. Second, [step 2]. Third, [step 3]. Finally, [step 4].'"
                                    ),
                                }
                            ]
                            for h_turn in self.history[-6:]:
                                h_role = "assistant" if h_turn.get("role") == "model" else "user"
                                h_text = "".join([p.get("text", "") for p in h_turn.get("parts", [])])
                                if h_text:
                                    groq_msgs.append({"role": h_role, "content": h_text})
                            groq_msgs.append({"role": "user", "content": transcript})

                            g_payload = {
                                "model": "qwen/qwen3.8-27b",
                                "messages": groq_msgs,
                                "max_tokens": max_toks,
                                "temperature": 0.3,
                            }
                            g_req = urllib.request.Request(
                                "https://api.groq.com/openai/v1/chat/completions",
                                data=json.dumps(g_payload).encode("utf-8"),
                                headers={
                                    "Authorization": f"Bearer {groq_key}",
                                    "Content-Type": "application/json",
                                    "User-Agent": "Mozilla/5.0",
                                },
                            )
                            with urllib.request.urlopen(g_req, timeout=4) as g_resp:
                                g_data = json.loads(g_resp.read().decode("utf-8"))
                            answer_text = g_data["choices"][0]["message"]["content"].strip()
                        except Exception as ge:
                            print(f"[DaemonLive] Groq fast model failed, falling back to Gemini: {ge}")

                    # 2. Fall back to Gemini (or for visual cursor inspection)
                    if not answer_text and gemini_key:
                        payload = {
                            "contents": contents,
                            "systemInstruction": sys_instruction,
                            "generationConfig": {"maxOutputTokens": max_toks, "temperature": 0.3}
                        }
                        data_bytes = json.dumps(payload).encode("utf-8")

                        models = [
                            "gemini-flash-lite-latest",
                            "gemini-3.5-flash-lite",
                            "gemini-3.1-flash-lite",
                        ]

                        for model in models:
                            try:
                                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}"
                                req = urllib.request.Request(url, data=data_bytes, headers={"Content-Type": "application/json"}, method="POST")
                                with urllib.request.urlopen(req, timeout=5) as resp:
                                    data = json.loads(resp.read().decode("utf-8"))
                                answer_text = data["candidates"][0]["content"]["parts"][0]["text"]
                                if answer_text:
                                    break
                            except Exception as me:
                                log_layer(1, f"Daemon Live model {model} failed: {me}")
                                continue

                    if not answer_text:
                        raise RuntimeError("All Daemon Live AI models failed.")

                    clean_ans = clean_spoken_text(answer_text)

                    # Append to conversational memory
                    self.history.append({"role": "user", "parts": [{"text": transcript}]})
                    self.history.append({"role": "model", "parts": [{"text": clean_ans}]})

                    # 3. Speak and loop continuously strictly AFTER speech completes
                    def _on_speech_finished_loop():
                        if not self.is_active:
                            self.on_state_change("IDLE", "Ready • Hold Ctrl+Alt to speak")
                            return

                        # 250ms echo cancellation cooldown to ensure audio driver buffer is silent
                        time.sleep(0.25)
                        if self.is_active:
                            print("[DaemonLive] Speech finished: looping back to continuous listening...")
                            self.on_state_change("LISTENING", "Daemon Live • Listening...")
                            self._safe_start_listening()

                    def _on_speech_start():
                        if self.is_active:
                            self.on_state_change("SPEAKING", clean_ans)

                    # Update status to processing until the first audio packet starts playing
                    self.on_state_change("PROCESSING", "Responding...")
                    tts_engine.speak(clean_ans, on_start=_on_speech_start, on_finish=_on_speech_finished_loop)

                except Exception as e:
                    log_layer(1, f"Daemon Live error: {e}")
                    print(f"[DaemonLive] Error during turn: {e}")
                    if self.is_active:
                        recovery_text = "I'm listening, go ahead."
                        def _on_err_start():
                            if self.is_active:
                                self.on_state_change("SPEAKING", recovery_text)
                        def _on_err_done():
                            time.sleep(0.2)
                            if self.is_active:
                                self.on_state_change("LISTENING", "Daemon Live • Listening...")
                                self._safe_start_listening()
                        tts_engine.speak(recovery_text, on_start=_on_err_start, on_finish=_on_err_done)

        threading.Thread(target=_worker, daemon=True).start()

    def _resume_listening_after_delay(self, delay: float = 1.0):
        def _res():
            time.sleep(delay)
            if self.is_active:
                self.on_state_change("LISTENING", "Daemon Live • Listening...")
                self._safe_start_listening()
        threading.Thread(target=_res, daemon=True).start()
