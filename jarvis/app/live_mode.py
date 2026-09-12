"""
JARVIS Gemini Live Mode Session Manager
"""

import threading
import json
import urllib.request
import base64
from typing import Callable
from jarvis.app.config import config
from jarvis.tools.vision_tool import VisionTool
from jarvis.tools.screen_tool import ScreenTool
from jarvis.voice.text_to_speech import tts_engine
from jarvis.utils.text_cleaner import clean_spoken_text
from jarvis.utils.cursor_logger import log_layer

class LiveSessionManager:
    def __init__(self, on_state_change: Callable[[str, str], None], start_listening_callback: Callable[[], None]):
        self.is_active = False
        self.history = []
        self.vision = VisionTool()
        self.screen_tool = ScreenTool()
        self.on_state_change = on_state_change
        self.start_listening = start_listening_callback

    def toggle(self):
        if self.is_active:
            self.stop()
        else:
            self.start()

    def start(self):
        self.is_active = True
        self.history = []
        self.on_state_change("LISTENING", "Live Mode active • Speak naturally!")
        # Trigger the first listen
        self.start_listening()

    def stop(self):
        self.is_active = False
        if tts_engine.is_speaking():
            tts_engine.stop()
        self.on_state_change("IDLE", "Ready • Hold Ctrl+Alt to speak")

    def process_turn(self, transcript: str):
        if not self.is_active:
            return

        self.on_state_change("PROCESSING", f"'{transcript}'")
        
        def _worker():
            try:
                # 1. Grab cursor region & screen context
                log_layer(3, "Capturing cursor ROI and screen for Live Mode context")
                cursor_bytes, text_hint = self.screen_tool.capture_cursor_region_bytes(radius=280)
                
                # 2. Build Gemini prompt
                gemini_key = config.get("gemini_api_key")
                if not gemini_key:
                    self.on_state_change("ERROR", "Gemini API Key missing for Live Mode.")
                    return
                
                contents = []
                # Inject rolling history (last 6 turns)
                for turn in self.history[-6:]:
                    contents.append(turn)
                    
                # Current user turn
                prompt_content = f"User says: {transcript}"
                if text_hint:
                    prompt_content += f"\n[Text directly under user cursor: '{text_hint}']"

                user_parts = [{"text": prompt_content}]

                if cursor_bytes:
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
                            "You are JARVIS, a warm, witty, remarkably natural human companion in live voice conversation. "
                            "You and the user are talking back and forth like Gemini Live. "
                            "You receive real-time snapshots of what is right under their cursor, including UI element text. "
                            "RULES:\n"
                            "1. Talk like a real person, not a robot or assistant. Never say 'How can I help', 'As an AI', or mission jargon.\n"
                            "2. Keep answers concise and snappy: 1 to 2 spoken sentences (under 35 words total) so chat is fast.\n"
                            "3. When the user asks 'what is this', 'read this', or points at anything on screen, directly explain what is at their cursor.\n"
                            "4. No markdown, no asterisks, no bullets. Plain spoken conversation only."
                        )
                    }]
                }
                
                payload = {
                    "contents": contents,
                    "systemInstruction": sys_instruction,
                    "generationConfig": {"maxOutputTokens": 140, "temperature": 0.4}
                }
                
                data_bytes = json.dumps(payload).encode("utf-8")
                
                # Active high-speed Gemini models with automatic failover
                models = [
                    "gemini-flash-lite-latest",
                    "gemini-3.5-flash",
                    "gemini-3.5-flash-lite",
                    "gemini-3.1-flash-lite",
                    "gemini-3.6-flash",
                    "gemini-flash-latest",
                ]
                
                answer_text = None
                for model in models:
                    try:
                        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}"
                        req = urllib.request.Request(url, data=data_bytes, headers={"Content-Type": "application/json"}, method="POST")
                        with urllib.request.urlopen(req, timeout=8) as resp:
                            data = json.loads(resp.read().decode("utf-8"))
                        answer_text = data["candidates"][0]["content"]["parts"][0]["text"]
                        if answer_text:
                            break
                    except Exception as me:
                        log_layer(1, f"Live Mode model {model} failed: {me}")
                        continue
                
                if not answer_text:
                    raise RuntimeError("All Live Mode Gemini models failed.")
                    
                clean_ans = clean_spoken_text(answer_text)
                
                # Append to history
                self.history.append({"role": "user", "parts": [{"text": transcript}]})
                self.history.append({"role": "model", "parts": [{"text": clean_ans}]})
                
                # 3. Speak and loop strictly AFTER speech completes
                def _on_speech_finished_loop():
                    if self.is_active:
                        self.on_state_change("LISTENING", "Listening...")
                        self.start_listening()
                    else:
                        self.on_state_change("IDLE", "Ready • Hold Ctrl+Alt to speak")

                self.on_state_change("SPEAKING", clean_ans)
                tts_engine.speak(clean_ans, on_finish=_on_speech_finished_loop)
                
            except Exception as e:
                log_layer(1, f"Live Mode error: {e}")
                self.on_state_change("IDLE", "Sorry, I missed that. Say again?")
                if self.is_active:
                    import time
                    time.sleep(1.0)
                    self.on_state_change("LISTENING", "Listening...")
                    self.start_listening()

        threading.Thread(target=_worker, daemon=True).start()
