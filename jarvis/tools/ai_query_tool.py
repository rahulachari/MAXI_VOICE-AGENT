"""
JARVIS AI Query Tool
Answers informational questions without executing desktop automation actions.
"""

import json
import urllib.request
from .base import BaseTool, ToolResult
from jarvis.app.config import config


class AIQueryTool(BaseTool):
    name = "AIQueryTool"
    description = "Provides concise, spoken explanations for general knowledge questions."

    def execute(self, action: str, **kwargs) -> ToolResult:
        query = kwargs.get("query", "")
        precomputed = kwargs.get("answer")
        from jarvis.voice.text_to_speech import clean_spoken_text

        if precomputed:
            cleaned = clean_spoken_text(precomputed)
            return ToolResult(status="SUCCESS", message=cleaned, data={"query": query, "answer": cleaned})

        if not query:
            return ToolResult(status="FAILED", message="No query provided.")

        gemini_key = config.get("gemini_api_key")
        if gemini_key:
            from jarvis.utils.text_cleaner import clean_spoken_text, clean_for_plain_text

            models = ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.7-flash"]
            payload = {
                "contents": [{"parts": [{"text": query}]}],
                "systemInstruction": {
                    "parts": [{
                        "text": (
                            "You are JARVIS, an articulate personal AI voice operating system assistant. "
                            "Answer the user concisely in 2 to 3 natural spoken sentences. "
                            "NEVER include markdown symbols, bullets, asterisks, hashtags, or code blocks. "
                            "Speak with human warmth, fluency, and direct clarity."
                        )
                    }]
                },
                "generationConfig": {"maxOutputTokens": 300, "temperature": 0.4},
            }
            data_bytes = json.dumps(payload).encode("utf-8")

            for model in models:
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}"
                    req = urllib.request.Request(
                        url,
                        data=data_bytes,
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )
                    with urllib.request.urlopen(req, timeout=8) as resp:
                        data = json.loads(resp.read().decode("utf-8"))
                    answer_text = data["candidates"][0]["content"]["parts"][0]["text"]
                    clean_spoken = clean_spoken_text(answer_text)
                    clean_plain = clean_for_plain_text(answer_text, target="plain")
                    return ToolResult(
                        status="SUCCESS",
                        message=clean_spoken,
                        data={"query": query, "answer": clean_plain, "full_details": clean_plain},
                    )
                except Exception as e:
                    err_str = str(e)
                    if "429" in err_str:
                        continue
                    print(f"[AIQueryTool] Model {model} failed: {e}")

            # If all cloud models rate-limited (429)
            return ToolResult(
                status="SUCCESS",
                message=f"Regarding {query}, your cloud AI quota is momentarily rate-limited. Please allow a moment before asking another complex query.",
                data={"query": query, "error": "rate_limited"},
            )

        return ToolResult(status="SUCCESS", message=f"I heard your question about '{query}'. Please configure your Gemini API key for cloud reasoning.")

