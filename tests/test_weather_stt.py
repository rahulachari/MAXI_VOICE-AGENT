import pytest
from jarvis.tools.weather_tool import WeatherTool
from jarvis.voice.speech_to_text import post_process_transcript
from jarvis.intelligence.local_engine import LocalSemanticEngine
from jarvis.intelligence.intent import IntentCategory


def test_post_process_transcript_phonetics():
    assert post_process_transcript("what is the whether today") == "what is the weather today"
    assert post_process_transcript("tell me whether in Mumbai") == "tell me weather in Mumbai"
    assert post_process_transcript("Java open YouTube") == "Jarvis open YouTube"
    assert post_process_transcript("open u tube") == "open YouTube"
    assert post_process_transcript("launch vs code") == "launch VS Code"
    assert post_process_transcript("open task mgr") == "open Task Manager"


def test_weather_tool_time_and_date():
    tool = WeatherTool()
    time_res = tool.get_time()
    assert time_res.status == "SUCCESS"
    assert "time" in time_res.data
    assert "day" in time_res.data

    date_res = tool.get_date()
    assert date_res.status == "SUCCESS"
    assert "date" in date_res.data


def test_local_engine_weather_and_time():
    w_intent = LocalSemanticEngine.parse("what is the weather today")
    assert w_intent is not None
    assert w_intent.category == IntentCategory.WEATHER
    assert w_intent.action == "get_weather"

    t_intent = LocalSemanticEngine.parse("what time is it")
    assert t_intent is not None
    assert t_intent.category == IntentCategory.TIME
    assert t_intent.action == "get_time"

    d_intent = LocalSemanticEngine.parse("what's today's date")
    assert d_intent is not None
    assert d_intent.category == IntentCategory.TIME
    assert d_intent.action == "get_date"
