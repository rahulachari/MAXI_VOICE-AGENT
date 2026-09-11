import pytest
from jarvis.intelligence.router import CommandRouter
from jarvis.intelligence.intent import IntentCategory


def test_router_offline_dispatch():
    router = CommandRouter()
    intent, result = router.route_and_execute("stop")
    assert intent.category == IntentCategory.CANCEL
    assert result.status == "CANCELLED"


def test_router_requires_confirmation():
    router = CommandRouter()
    intent, result = router.route_and_execute("delete the file confidential.txt")
    assert intent.category == IntentCategory.FILE_DELETE
    assert result.requires_confirmation is True
    assert "confidential.txt" in result.confirmation_prompt
