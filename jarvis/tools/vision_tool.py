"""
JARVIS Vision Tool
Analyzes screen captures, extracts error messages via OCR and AI reasoning, and answers visual queries.
"""

import os
from PIL import Image
import pytesseract
from .base import BaseTool, ToolResult
from jarvis.app.config import config


class VisionTool(BaseTool):
    name = "VisionTool"
    description = "Understands screen content and diagnoses errors."

    def execute(self, action: str, **kwargs) -> ToolResult:
        image_path = kwargs.get("image_path", "")
        prompt = kwargs.get("prompt", "Explain what is visible.")

        if not image_path or not os.path.exists(image_path):
            return ToolResult(status="FAILED", message="No valid screen image provided.")

        try:
            # 1. Extract text from the image using OCR
            img = Image.open(image_path)
            extracted_text = ""
            try:
                extracted_text = pytesseract.image_to_string(img).strip()
            except Exception:
                pass

            # 2. Use AI provider to synthesize a clear response
            groq_key = config.get("groq_api_key")
            if groq_key:
                from groq import Groq
                client = Groq(api_key=groq_key)

                system_prompt = (
                    "You are JARVIS. The user asked a question about their active computer screen. "
                    "Based on the OCR text and context provided, answer concisely in 1-2 spoken sentences."
                )
                user_msg = f"User query: '{prompt}'.\nOCR Text extracted from screen:\n{extracted_text[:1500]}"

                resp = client.chat.completions.create(
                    model=config.get("ai_model", "openai/gpt-oss-120b"),
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_msg},
                    ],
                    max_tokens=150,
                )
                answer = resp.choices[0].message.content.strip()
                return ToolResult(status="SUCCESS", message=answer, data={"ocr": extracted_text, "explanation": answer})

            if extracted_text:
                summary = extracted_text[:120].replace("\n", " ")
                return ToolResult(status="SUCCESS", message=f"Screen text: {summary}", data={"ocr": extracted_text})

            return ToolResult(status="SUCCESS", message="I analyzed your screen.", data={})

        except Exception as e:
            return ToolResult(status="FAILED", message=f"Vision analysis failed: {e}", error=str(e))
