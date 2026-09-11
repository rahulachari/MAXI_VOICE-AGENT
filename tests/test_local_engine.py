import pytest
from jarvis.intelligence.local_engine import LocalSemanticEngine
from jarvis.intelligence.intent import IntentCategory


def test_youtube_navigation():
    for phrase in ["Open YouTube", "launch youtube", "can you open youtube", "take me to YouTube"]:
        intent = LocalSemanticEngine.parse(phrase)
        assert intent is not None, f"Failed on: {phrase}"
        assert intent.category == IntentCategory.WEB_NAVIGATION
        assert intent.target == "YouTube"
        assert intent.action == "open_youtube"


def test_youtube_search():
    intent = LocalSemanticEngine.parse("search youtube for Python tutorials")
    assert intent is not None
    assert intent.category == IntentCategory.WEB_SEARCH
    assert intent.target == "YouTube"
    assert intent.action == "search_youtube"
    assert "python tutorials" in intent.params["query"].lower()


def test_app_launch_and_close():
    launch_intent = LocalSemanticEngine.parse("Open Notepad")
    assert launch_intent is not None
    assert launch_intent.category == IntentCategory.APP_LAUNCH
    assert launch_intent.params["app_name"] == "notepad"

    close_intent = LocalSemanticEngine.parse("close chrome")
    assert close_intent is not None
    assert close_intent.category == IntentCategory.APP_CLOSE
    assert close_intent.params["app_name"] == "chrome"


def test_system_controls():
    lock_intent = LocalSemanticEngine.parse("lock my pc")
    assert lock_intent is not None
    assert lock_intent.category == IntentCategory.SYSTEM_CONTROL
    assert lock_intent.action == "lock_pc"

    scroll_intent = LocalSemanticEngine.parse("scroll down")
    assert scroll_intent is not None
    assert scroll_intent.category == IntentCategory.BROWSER_ACTION
    assert scroll_intent.action == "scroll_down"


def test_destructive_confirmation():
    del_intent = LocalSemanticEngine.parse("delete the file old_report.pdf")
    assert del_intent is not None
    assert del_intent.category == IntentCategory.FILE_DELETE
    assert del_intent.requires_confirmation is True
    assert "old_report.pdf" in del_intent.params["target"]
