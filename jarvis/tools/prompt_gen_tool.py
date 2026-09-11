"""
JARVIS Prompt Generation & Engineering Tool
Generates elite, structured, production-grade prompts for any application,
system, or concept, complete with copy-to-clipboard button in the notch.
"""

import json
import urllib.request
from typing import Dict, Any
from .base import BaseTool, ToolResult
from jarvis.app.config import config
from jarvis.utils.text_cleaner import clean_for_plain_text


class PromptGeneratorTool(BaseTool):
    name = "PromptGeneratorTool"
    description = "Generates and polishes high-performance AI prompts with direct copy-to-clipboard support."

    def execute(self, action: str, **kwargs) -> ToolResult:
        topic = kwargs.get("topic", "").strip()
        if not topic:
            return ToolResult(status="FAILED", message="What topic or application would you like a prompt for?")

        return self.generate_prompt(topic)

    def generate_prompt(self, topic: str) -> ToolResult:
        api_key = config.get("gemini_api_key")
        model = "gemini-3.1-flash-lite"

        system_prompt = (
            "You are an elite Prompt Engineer. When given a topic or app concept, generate a comprehensive, "
            "production-grade system prompt or user prompt designed to get optimal output from AI models. "
            "Structure it cleanly with:\n"
            "1. Goal & Role\n"
            "2. Core Requirements\n"
            "3. Constraints & Guidelines\n"
            "4. Expected Output Format\n"
            "Write in clear, articulate text. Do not use markdown headers (###) or messy asterisks."
        )

        user_query = f"Create an exceptional, ready-to-use prompt for: '{topic}'."

        if api_key:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
                payload = {
                    "system_instruction": {"parts": [{"text": system_prompt}]},
                    "contents": [{"parts": [{"text": user_query}]}],
                    "generationConfig": {"temperature": 0.4, "maxOutputTokens": 600},
                }
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    res_data = json.loads(resp.read().decode("utf-8"))
                    generated_text = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    clean_text = clean_for_plain_text(generated_text, target="plain")

                    spoken = f"I've generated a complete polished prompt for {topic}. You can review it in the notch and click Copy Prompt."
                    return ToolResult(
                        status="SUCCESS",
                        message=spoken,
                        data={
                            "is_prompt_card": True,
                            "topic": topic.title(),
                            "prompt_text": clean_text,
                            "full_details": f"Generated Prompt for {topic.title()}:\n\n{clean_text}",
                        },
                    )
            except Exception as e:
                print(f"[PromptGenTool] Gemini call error: {e}")

        # Fallback offline template if API is temporarily unavailable
        fallback_prompt = (
            f"You are an expert specialist developing: {topic.title()}.\n\n"
            "Responsibilities:\n"
            f"- Design, architect, and implement high-efficiency workflows for {topic.title()}.\n"
            "- Ensure minimal latency, user-friendly UI interactions, and robust state management.\n"
            "- Implement comprehensive validation, edge-case handling, and elegant feedback.\n\n"
            "Output Format:\n"
            "Provide clean code implementations, clear step-by-step guidance, and concise documentation."
        )

        return ToolResult(
            status="SUCCESS",
            message=f"I've crafted a prompt template for {topic}. Tap Copy Prompt in the notch to copy it.",
            data={
                "is_prompt_card": True,
                "topic": topic.title(),
                "prompt_text": fallback_prompt,
                "full_details": fallback_prompt,
            },
        )
