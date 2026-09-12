import pytest
from jarvis.intelligence.router import CommandRouter
from jarvis.app.lifecycle import LifecycleManager
from jarvis.tools.browser_tool import BrowserTool
from jarvis.tools.weather_tool import WeatherTool

def test_clean_for_display_strips_urls_and_emojis():
    raw_text = "▶️ Playing: yahoo yahoo song\nURL: https://www.youtube.com/watch?v=mMKMJk8XdHc&autoplay=1"
    cleaned = LifecycleManager._clean_for_display(raw_text)
    assert "https://" not in cleaned
    assert "URL:" not in cleaned
    assert "▶" not in cleaned
    assert "Playing: yahoo yahoo song" in cleaned

def test_browser_tool_play_youtube_has_no_url_in_details():
    tool = BrowserTool()
    res = tool.execute("play_youtube", query="test track")
    assert res.is_success()
    assert "URL:" not in res.data.get("full_details", "")
    assert "▶" not in res.data.get("full_details", "")
    assert "Playing: test track" in res.data.get("full_details", "")

def test_weather_tool_clean_output():
    tool = WeatherTool()
    res = tool.execute("get_weather", location="Chittoor")
    assert res.is_success()
    details = res.data.get("full_details", "")
    assert "In Chittoor" in details
    assert "°C" in details
    assert "🌤" not in details
    assert "•" not in details

def test_router_handles_informational_query():
    router = CommandRouter()
    intent, res = router.route_and_execute("what is the IMDb rating of Radhe Shyam")
    assert res.is_success()
    cleaned = LifecycleManager._clean_for_display(res.message)
    assert len(cleaned) > 10
    # Must not be a placeholder comment
    assert not any(p in cleaned.lower() for p in ["searching the web", "searching google", "looking that up"])
