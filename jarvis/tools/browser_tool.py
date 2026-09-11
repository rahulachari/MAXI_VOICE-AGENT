"""
JARVIS Browser Automation Tool
Controls web navigation, YouTube searches, page scrolling, and tab management with action verification.
"""

import time
import pyautogui
from .base import BaseTool, ToolResult
from jarvis.adapters.chrome_adapter import ChromeAdapter
from jarvis.adapters.youtube_adapter import YouTubeAdapter


class BrowserTool(BaseTool):
    name = "BrowserTool"
    description = "Automates browser navigation, YouTube searches, tabs, and page scrolling."

    def execute(self, action: str, **kwargs) -> ToolResult:
        action = action.lower().strip()

        if action == "open_youtube":
            url = YouTubeAdapter.get_home_url()
            ChromeAdapter.open_url(url)
            time.sleep(0.5)
            ChromeAdapter.focus_chrome()
            return ToolResult(status="SUCCESS", message="YouTube is open.", data={"url": url})

        elif action == "search_youtube":
            query = kwargs.get("query", "")
            if not query:
                return ToolResult(status="FAILED", message="What would you like to search on YouTube?")
            url = YouTubeAdapter.get_search_url(query)
            ChromeAdapter.open_url(url)
            time.sleep(0.5)
            ChromeAdapter.focus_chrome()
            return ToolResult(status="SUCCESS", message=f"I've searched for {query} on YouTube.", data={"query": query, "url": url})

        elif action == "search_google":
            query = kwargs.get("query", "")
            if not query:
                return ToolResult(status="FAILED", message="What would you like to search on Google?")
            import urllib.parse
            url = f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}"
            ChromeAdapter.open_url(url)
            time.sleep(0.5)
            ChromeAdapter.focus_chrome()
            return ToolResult(status="SUCCESS", message=f"I've searched for {query}.", data={"query": query, "url": url})

        elif action == "open_url":
            url = kwargs.get("url", "")
            if not url.startswith("http://") and not url.startswith("https://"):
                url = f"https://{url}"
            ChromeAdapter.open_url(url)
            time.sleep(0.5)
            ChromeAdapter.focus_chrome()
            return ToolResult(status="SUCCESS", message=f"Navigated to {url}.", data={"url": url})

        elif action in ["scroll_down", "scroll"]:
            if not ChromeAdapter.focus_chrome():
                return ToolResult(status="FAILED", message="I couldn't find an open browser window.")
            pyautogui.press("pagedown")
            return ToolResult(status="SUCCESS", message="Scrolled down.")

        elif action == "scroll_up":
            if not ChromeAdapter.focus_chrome():
                return ToolResult(status="FAILED", message="I couldn't find an open browser window.")
            pyautogui.press("pageup")
            return ToolResult(status="SUCCESS", message="Scrolled up.")

        elif action == "new_tab":
            if not ChromeAdapter.focus_chrome():
                return ToolResult(status="FAILED", message="I couldn't find an open browser window.")
            pyautogui.hotkey("ctrl", "t")
            return ToolResult(status="SUCCESS", message="Opened a new tab.")

        elif action == "close_tab":
            if not ChromeAdapter.focus_chrome():
                return ToolResult(status="FAILED", message="I couldn't find an open browser window.")
            pyautogui.hotkey("ctrl", "w")
            return ToolResult(status="SUCCESS", message="Closed the tab.")

        elif action == "refresh":
            if not ChromeAdapter.focus_chrome():
                return ToolResult(status="FAILED", message="I couldn't find an open browser window.")
            pyautogui.press("f5")
            return ToolResult(status="SUCCESS", message="Refreshed page.")

        elif action == "back":
            if not ChromeAdapter.focus_chrome():
                return ToolResult(status="FAILED", message="I couldn't find an open browser window.")
            pyautogui.hotkey("alt", "left")
            return ToolResult(status="SUCCESS", message="Navigated back.")

        elif action == "forward":
            if not ChromeAdapter.focus_chrome():
                return ToolResult(status="FAILED", message="I couldn't find an open browser window.")
            pyautogui.hotkey("alt", "right")
            return ToolResult(status="SUCCESS", message="Navigated forward.")

        elif action == "play_pause":
            if not ChromeAdapter.focus_chrome():
                return ToolResult(status="FAILED", message="I couldn't find an open browser window.")
            pyautogui.press("space")
            return ToolResult(status="SUCCESS", message="Toggled playback.")

        return ToolResult(status="FAILED", message=f"Unknown browser action: {action}")
