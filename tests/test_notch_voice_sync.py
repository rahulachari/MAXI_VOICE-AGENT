import pytest
from jarvis.intelligence.intent import Intent, IntentCategory
from jarvis.intelligence.provider import AIProvider
from jarvis.tools.ai_query_tool import AIQueryTool


def test_ai_query_tool_synchronization():
    tool = AIQueryTool()
    sample_answer = "The average retail price for plain cashew kernels typically ranges from 800 to 1200 per kg."
    res = tool.execute("query", query="cashew price", answer=sample_answer, full_details=sample_answer)
    assert res.is_success()
    assert res.message == sample_answer
    assert res.data["answer"] == sample_answer
    assert res.data["full_details"] == sample_answer


def test_provider_ai_query_synchronization():
    provider = AIProvider()
    raw_json = '''{
        "category": "AI_QUERY",
        "target": "",
        "action": "query",
        "params": {},
        "requires_confirmation": false,
        "spoken_response": "Broken cashews generally cost around 600 to 750 per kg.",
        "full_details": "Broken cashews generally cost around 600 to 750 per kg."
    }'''
    intent = provider._parse_json_to_intent(raw_json, "cashew broken price")
    assert intent.category == IntentCategory.AI_QUERY
    assert intent.confirmation_prompt == "Broken cashews generally cost around 600 to 750 per kg."
    assert intent.params["full_details"] == "Broken cashews generally cost around 600 to 750 per kg."


def test_notch_buttons_presence():
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    from jarvis.ui.notch import VoiceOSNotch

    notch = VoiceOSNotch()
    # Verify Copy button exists and has vector icon (no emoji text)
    assert hasattr(notch, "btn_copy")
    assert notch.btn_copy is not None
    assert "Copy" not in notch.btn_copy.text()
    assert not notch.btn_copy.icon().isNull()

    # Verify Voice Mute/Unmute button exists and has vector icon (no emoji text)
    assert hasattr(notch, "btn_voice")
    assert notch.btn_voice is not None
    assert "Mute" not in notch.btn_voice.text()
    assert not notch.btn_voice.icon().isNull()

    # Verify Liquid Orb Gemini AI button exists
    assert hasattr(notch, "orb")
    assert hasattr(notch, "collapsed_orb")

    # Verify NO Like or Dislike buttons exist
    assert not hasattr(notch, "btn_like")
    assert not hasattr(notch, "btn_dislike")
    assert not hasattr(notch, "btn_up")
    assert not hasattr(notch, "btn_down")

    # Test copy method
    notch.prompt_label.setText("Test answer description")
    notch._on_copy_clicked()
    clipboard = QApplication.clipboard()
    assert clipboard.text() == "Test answer description"

    # Test voice mute toggle (vector icon, no text words)
    notch.set_voice_active(True)
    assert notch._voice_active is True
    assert "Mute" not in notch.btn_voice.text()
    assert not notch.btn_voice.icon().isNull()

    # Verify dedicated Live continuous conversation button exists
    assert hasattr(notch, "btn_live")
    assert notch.btn_live is not None
    assert "Live" in notch.btn_live.text()

    # Verify scrollbar bars are completely turned off
    from PySide6.QtCore import Qt
    assert notch.scroll_area.verticalScrollBarPolicy() == Qt.ScrollBarAlwaysOff
    assert notch.scroll_area.horizontalScrollBarPolicy() == Qt.ScrollBarAlwaysOff

    notch.close()


def test_ai_provider_conversation_memory():
    provider = AIProvider()
    assert hasattr(provider, "conversation_memory")
    assert isinstance(provider.conversation_memory, list)
    assert len(provider.conversation_memory) == 0

    # Simulate parsing a response
    raw_json = '''{
        "category": "AI_QUERY",
        "target": "",
        "action": "query",
        "params": {"query": "What is AGI?"},
        "spoken_response": "AGI refers to Artificial General Intelligence.",
        "full_details": "AGI refers to Artificial General Intelligence."
    }'''
    provider._parse_json_to_intent(raw_json, "What is AGI?")
    # Verify conversational memory now has user turn and model response
    assert len(provider.conversation_memory) == 2
    assert provider.conversation_memory[0]["role"] == "user"
    assert "What is AGI?" in provider.conversation_memory[0]["parts"][0]["text"]
    assert provider.conversation_memory[1]["role"] == "model"

    # Simulate follow-up question
    raw_json_2 = '''{
        "category": "AI_QUERY",
        "target": "",
        "action": "query",
        "params": {"query": "Can you summarize that?"},
        "spoken_response": "In short, AGI is human-level machine intelligence.",
        "full_details": "In short, AGI is human-level machine intelligence."
    }'''
    provider._parse_json_to_intent(raw_json_2, "Can you summarize that?")
    assert len(provider.conversation_memory) == 4

    provider.clear_memory()
    assert len(provider.conversation_memory) == 0
