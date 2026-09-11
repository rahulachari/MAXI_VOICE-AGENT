"""
JARVIS AI Query Tool
Answers informational questions without executing desktop automation actions.
"""

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

        groq_key = config.get("groq_api_key")
        if groq_key:
            try:
                from groq import Groq
                client = Groq(api_key=groq_key)
                resp = client.chat.completions.create(
                    model=config.get("ai_model", "openai/gpt-oss-120b"),
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are JARVIS VoiceOS, an intelligent AI companion. "
                                "Answer the user concisely in 1 to 2 spoken sentences. Be direct, conversational, and articulate. "
                                "Never include markdown symbols, bullets, asterisks, code blocks, or software version numbers."
                            ),
                        },
                        {"role": "user", "content": query},
                    ],
                    max_tokens=300,
                    temperature=0.3,
                )
                answer = clean_spoken_text(resp.choices[0].message.content or "")
                return ToolResult(status="SUCCESS", message=answer, data={"query": query, "answer": answer})
            except Exception as e:
                return ToolResult(status="FAILED", message=f"AI service error: {e}", error=str(e))

        return ToolResult(status="SUCCESS", message=f"I heard your question about '{query}'. Please configure your AI key for cloud reasoning.")
