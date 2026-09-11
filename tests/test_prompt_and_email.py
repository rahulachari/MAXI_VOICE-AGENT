"""
Unit tests for Prompt Generation, Email Reader Tool, and Notch Card widgets.
"""

import pytest
from jarvis.intelligence.intent import IntentCategory
from jarvis.intelligence.local_engine import LocalSemanticEngine
from jarvis.intelligence.router import CommandRouter


def test_prompt_intent_parsing():
    queries = [
        "give me a prompt for tagged box",
        "give a prompt for tagged box",
        "prompt for tagged box",
        "generate a prompt for a health diagnosis app",
        "create a prompt about customer service bot",
    ]
    for q in queries:
        intent = LocalSemanticEngine.parse(q)
        assert intent is not None, f"Failed to parse prompt query: {q}"
        assert intent.category == IntentCategory.PROMPT_GEN
        assert intent.action == "generate_prompt"
        assert len(intent.params.get("topic", "")) > 0


def test_email_read_intent_parsing():
    queries = [
        "read my gmails",
        "check my emails",
        "read emails",
        "read gmail",
        "check my inbox",
        "show my emails",
    ]
    for q in queries:
        intent = LocalSemanticEngine.parse(q)
        assert intent is not None, f"Failed to parse email query: {q}"
        assert intent.category == IntentCategory.EMAIL
        assert intent.action == "read_emails"


def test_router_prompt_generation():
    router = CommandRouter()
    intent, result = router.route_and_execute("prompt for tagged box")
    assert intent.category == IntentCategory.PROMPT_GEN
    assert result.is_success()
    assert result.data.get("is_prompt_card") is True
    assert "tagged box" in result.data.get("topic", "").lower()
    assert len(result.data.get("prompt_text", "")) > 20
