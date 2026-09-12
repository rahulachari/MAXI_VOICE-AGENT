"""
JARVIS Vision Tool
Analyzes in-memory screen captures using Gemini Vision multimodal API.
Zero disk persistence: all image data is processed in memory and immediately discarded.
Includes fallback to Windows UI Automation element text hints and spoken explanations.
"""

import base64
import json
import urllib.request
from typing import Optional
from .base import BaseTool, ToolResult
from jarvis.app.config import config
from jarvis.utils.text_cleaner import clean_spoken_text, clean_for_plain_text
from jarvis.utils.cursor_logger import log_layer


class VisionTool(BaseTool):
    name = "VisionTool"
    description = "Understands in-memory screen content and cursor focus using Gemini Vision multimodal AI."

    def execute(self, action: str, **kwargs) -> ToolResult:
        image_bytes: Optional[bytes] = kwargs.get("image_bytes")
        image_path: Optional[str] = kwargs.get("image_path")
        prompt: str = kwargs.get("prompt", "What is at the cursor position and what does it say?")
        text_hint: str = kwargs.get("text_hint", "")

        # Backwards compatibility if image_path passed
        if not image_bytes and image_path:
            try:
                import os
                if os.path.exists(image_path):
                    with open(image_path, "rb") as f:
                        image_bytes = f.read()
            except Exception:
                pass

        action_name = (action or "").lower().strip()

        if action_name == "find_linkedin":
            b64_image = base64.b64encode(image_bytes).decode("utf-8") if image_bytes else ""
            return self._find_linkedin(b64_image, text_hint)

        if not image_bytes:
            log_layer(4, "No image bytes received for vision analysis", action=action_name, text_hint=bool(text_hint))
            if text_hint:
                return ToolResult(
                    status="SUCCESS",
                    message=f"I read the following text at your cursor: {text_hint}",
                    data={"explanation": text_hint, "full_details": text_hint},
                )
            return ToolResult(
                status="SUCCESS",
                message="I couldn't read your screen, but here's what I can tell you. Please make sure the window is visible and point your cursor directly over it.",
                data={"explanation": "Screen capture unavailable.", "full_details": "Screen capture unavailable."},
            )

        # In-memory base64 encoding
        b64_image = base64.b64encode(image_bytes).decode("utf-8")
        log_layer(4, "Starting content extraction", action=action_name, b64_len=len(b64_image), text_hint=text_hint[:60] if text_hint else "none")

        gemini_key = config.get("gemini_api_key")
        if gemini_key:
            res = self._analyze_with_gemini(b64_image, "image/jpeg", prompt, gemini_key)
            if res.is_success():
                log_layer(4, "Gemini vision analysis successful", summary=res.message[:80])
                return res

        # Fallback to UI Automation / OCR text hint if available
        if text_hint and text_hint.strip():
            log_layer(4, "Falling back to UI text hint", text=text_hint[:80])
            summary = clean_for_plain_text(text_hint, target="plain")
            return ToolResult(
                status="SUCCESS",
                message=f"I detected the following near your cursor: {summary[:180]}.",
                data={"explanation": summary, "full_details": summary},
            )

        log_layer(4, "Vision and text extraction both empty; providing spoken guidance fallback")
        return ToolResult(
            status="SUCCESS",
            message="I couldn't clearly read what's under your cursor. Could you point directly at the text or image and ask again?",
            data={"explanation": "Cursor context could not be resolved.", "full_details": "Cursor context could not be resolved from screen capture."},
        )

    def _find_linkedin(self, b64_image: str, text_hint: str = "") -> ToolResult:
        """Extracts person/company name near cursor and launches their LinkedIn search."""
        import urllib.parse
        import urllib.request
        import re
        from jarvis.utils.text_cleaner import clean_for_plain_text

        gemini_key = config.get("gemini_api_key")
        person_name = ""

        if gemini_key and b64_image:
            prompt = (
                "Extract the person's full name and company/title from the text visible near the center of the image. "
                "Respond strictly with 'Name - Company/Title'. If no name is clearly identifiable in the text, respond strictly with 'NO_NAME_FOUND'."
            )
            res = self._analyze_with_gemini(b64_image, "image/jpeg", prompt, gemini_key)
            if res.is_success():
                candidate = res.message.strip().replace('"', '').replace("'", "")
                if candidate and candidate != "NO_NAME_FOUND" and len(candidate) < 100:
                    person_name = candidate
                    log_layer(4, "Gemini identified person for LinkedIn", name=person_name)

        if not person_name and text_hint:
            raw_text = clean_for_plain_text(text_hint, target="plain")
            lines = [l.strip() for l in raw_text.split("\n") if l.strip()]
            if lines and len(lines[0]) < 60:
                person_name = lines[0]
                log_layer(4, "UI text hint provided name for LinkedIn", name=person_name)

        if not person_name or person_name == "NO_NAME_FOUND":
            log_layer(4, "No specific name identified in text.")
            return ToolResult(
                status="FAILED",
                message="I cannot identify this person from the image alone. Please point at their name in the text.",
            )

        direct_linkedin_url = f"https://www.linkedin.com/search/results/all/?keywords={urllib.parse.quote_plus(person_name)}"
        return ToolResult(
            status="REQUIRES_CONFIRMATION",
            message=f"I found {person_name}. Shall I open their LinkedIn profile?",
            requires_confirmation=True,
            confirmation_prompt=f"Open LinkedIn: {person_name}",
            data={"url": direct_linkedin_url, "full_details": f"Target: {direct_linkedin_url}"}
        )

    def _analyze_with_gemini(self, b64_image: str, mime_type: str, prompt: str, api_key: str) -> ToolResult:
        """Query Gemini Vision API in memory using active working models."""
        models = [
            "gemini-flash-lite-latest",
            "gemini-3.5-flash",
            "gemini-3.5-flash-lite",
            "gemini-3.1-flash-lite",
            "gemini-3.6-flash",
            "gemini-flash-latest",
        ]

        payload = {
            "contents": [{
                "parts": [
                    {
                        "text": (
                            f"{prompt}\n"
                            "Context: This is an in-memory capture of the user's screen centered on their cursor. "
                            "Explain what is shown or answer their question directly, clearly, and concisely in 2-3 sentences. "
                            "Do not use markdown symbols, bullet asterisks, or hashtags."
                        )
                    },
                    {
                        "inlineData": {
                            "mimeType": mime_type,
                            "data": b64_image,
                        }
                    },
                ]
            }],
            "systemInstruction": {
                "parts": [{
                    "text": (
                        "You are JARVIS, an elite desktop voice assistant. "
                        "Give concise, natural, spoken explanations about the user's screen or cursor focus. "
                        "Never use raw markdown formatting, asterisks, hashtags, or bullet points."
                    )
                }]
            },
            "generationConfig": {"maxOutputTokens": 300, "temperature": 0.2},
        }
        data_bytes = json.dumps(payload).encode("utf-8")

        for model in models:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
                req = urllib.request.Request(
                    url,
                    data=data_bytes,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read().decode("utf-8"))

                candidates = data.get("candidates", [])
                if not candidates:
                    continue
                parts = candidates[0].get("content", {}).get("parts", [])
                if not parts:
                    continue

                raw_answer = parts[0].get("text", "").strip()
                clean_spoken = clean_spoken_text(raw_answer)
                clean_plain = clean_for_plain_text(raw_answer, target="plain")
                return ToolResult(
                    status="SUCCESS",
                    message=clean_spoken,
                    data={"explanation": clean_plain, "full_details": clean_plain},
                )
            except Exception as e:
                err_str = str(e)
                log_layer(4, f"Model {model} attempt failed", error=err_str[:120])
                if "429" in err_str or "503" in err_str or "timed out" in err_str or "404" in err_str:
                    continue

        return ToolResult(status="FAILED", message="Cloud vision models are currently busy.")
