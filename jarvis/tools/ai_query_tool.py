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
        if action == "deep_explanation":
            return self._deep_explanation(kwargs.get("topic", ""))

        query = kwargs.get("query", "")
        precomputed = kwargs.get("answer")
        from jarvis.voice.text_to_speech import clean_spoken_text

        if precomputed:
            cleaned = clean_spoken_text(precomputed)
            full_det = kwargs.get("full_details") or cleaned
            return ToolResult(status="SUCCESS", message=cleaned, data={"query": query, "answer": cleaned, "full_details": full_det})

        if not query:
            return ToolResult(status="FAILED", message="No query provided.")

        gemini_key = config.get("gemini_api_key")
        if gemini_key:
            from jarvis.utils.text_cleaner import clean_spoken_text, clean_for_plain_text

            models = [
                "gemini-flash-lite-latest",
                "gemini-3.5-flash",
                "gemini-3.5-flash-lite",
                "gemini-3.1-flash-lite",
                "gemini-3.6-flash",
                "gemini-flash-latest",
            ]
            payload = {
                "contents": [{"parts": [{"text": query}]}],
                "systemInstruction": {
                    "parts": [{
                        "text": (
                            "You are JARVIS, a lightning-fast AI assistant like Google Assistant. "
                            "Give a direct, crisp answer in 1 to 2 spoken sentences (under 25 words total). "
                            "NEVER include markdown symbols, bullets, asterisks, hashtags, or conversational filler. "
                            "Answer directly so it can be spoken out loud immediately."
                        )
                    }]
                },
                "generationConfig": {"maxOutputTokens": 120, "temperature": 0.3},
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

    def _deep_explanation(self, topic: str) -> ToolResult:
        import urllib.parse
        import urllib.request
        import re
        from jarvis.utils.text_cleaner import clean_spoken_text
        from jarvis.utils.cursor_logger import log_layer

        if not topic:
            return ToolResult(status="FAILED", message="I need a topic to explain.")

        gemini_key = config.get("gemini_api_key")
        if not gemini_key:
            return ToolResult(status="FAILED", message="API key is required for deep explanations.")

        # 1. Scrape DDG for live context
        search_context = ""
        try:
            url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote_plus(topic)}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                html = response.read().decode('utf-8')
            
            snippets = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', html, re.IGNORECASE | re.DOTALL)
            if snippets:
                clean_snippets = [re.sub(r'<[^>]+>', '', s).strip() for s in snippets[:3]]
                search_context = "\n".join(clean_snippets)
                log_layer(4, "Deep Explanation search context retrieved", lines=len(clean_snippets))
        except Exception as e:
            log_layer(2, "DDG Search failed for deep explanation", error=str(e))

        # 2. Query Gemini
        prompt = (
            f"The user wants a deep explanation for: '{topic}'.\n\n"
            f"Here is some live search context (if relevant):\n{search_context}\n\n"
            "Provide two things in a strictly formatted JSON response:\n"
            "1. 'spoken_summary': A crisp, 2-3 sentence summary designed to be spoken aloud. No markdown.\n"
            "2. 'long_explanation': A highly detailed, well-organized explanation using Markdown headers (##) and bullet points. "
            "Cover what it is, how it works, and context (like business model or interview prep if relevant). Make it rich and structured for reading."
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.4, "responseMimeType": "application/json"},
        }
        data_bytes = json.dumps(payload).encode("utf-8")
        
        models = [
            "gemini-flash-lite-latest",
            "gemini-3.5-flash",
            "gemini-3.5-flash-lite",
            "gemini-3.1-flash-lite",
            "gemini-3.6-flash",
            "gemini-flash-latest",
        ]
        last_error = None
        
        for model in models:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}"
                req = urllib.request.Request(url, data=data_bytes, headers={"Content-Type": "application/json"}, method="POST")
                with urllib.request.urlopen(req, timeout=12) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                
                answer_text = data["candidates"][0]["content"]["parts"][0]["text"]
                parsed = json.loads(answer_text)
                    
                spoken_summary = clean_spoken_text(parsed.get("spoken_summary", f"Here is an explanation of {topic}."))
                long_explanation = parsed.get("long_explanation", "")
                
                return ToolResult(
                    status="SUCCESS",
                    message=spoken_summary,
                    data={"full_details": long_explanation, "topic": topic}
                )
            except Exception as e:
                last_error = e
                if "429" in str(e):
                    continue
                print(f"[AIQueryTool] Deep explanation model {model} failed: {e}")
                
        return ToolResult(status="FAILED", message=f"Failed to generate deep explanation. AI API rate limited (429). Please wait a moment.")
