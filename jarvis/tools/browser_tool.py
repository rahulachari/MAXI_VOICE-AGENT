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
            return ToolResult(
                status="SUCCESS",
                message="Opening YouTube for you.",
                data={"url": url, "full_details": "YouTube opened in browser."},
            )

        elif action == "play_youtube":
            query = kwargs.get("query", "")
            if not query:
                return ToolResult(status="FAILED", message="What would you like me to play on YouTube?")
            url = YouTubeAdapter.get_direct_play_url(query)
            ChromeAdapter.open_url(url)
            return ToolResult(
                status="SUCCESS",
                message=f"Playing {query} on YouTube.",
                data={"query": query, "url": url, "full_details": f"Playing: {query}"},
            )

        elif action == "search_youtube":
            query = kwargs.get("query", "")
            if not query:
                return ToolResult(status="FAILED", message="What would you like to search on YouTube?")
            url = YouTubeAdapter.get_search_url(query)
            ChromeAdapter.open_url(url)
            return ToolResult(
                status="SUCCESS",
                message=f"Searching YouTube for {query}.",
                data={"query": query, "url": url, "full_details": f"YouTube Search: {query}"},
            )

        elif action == "search_google":
            query = kwargs.get("query", "")
            if not query:
                return ToolResult(status="FAILED", message="What would you like to search on Google?")
            import urllib.parse
            url = f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}"
            ChromeAdapter.open_url(url)
            return ToolResult(
                status="SUCCESS",
                message=f"Searching Google for {query}.",
                data={"query": query, "url": url, "full_details": f"Google Search: {query}"},
            )

        elif action == "lucky_search":
            query = kwargs.get("query", "")
            if not query:
                return ToolResult(status="FAILED", message="What would you like to open?")
            import urllib.parse
            # DuckDuckGo 'I'm Feeling Lucky' equivalent uses !ducky bang
            url = f"https://duckduckgo.com/?q={urllib.parse.quote_plus('!ducky ' + query)}"
            ChromeAdapter.open_url(url)
            return ToolResult(
                status="SUCCESS",
                message=f"Opening {query}.",
                data={"query": query, "url": url, "full_details": f"Opening: {query}"},
            )
        elif action == "search_amazon":
            query = kwargs.get("query", "")
            if not query:
                return ToolResult(status="FAILED", message="What would you like to search on Amazon?")
            import urllib.parse
            url = f"https://www.amazon.in/s?k={urllib.parse.quote_plus(query)}"
            ChromeAdapter.open_url(url)
            return ToolResult(
                status="SUCCESS",
                message=f"Searching Amazon for {query}.",
                data={"query": query, "url": url, "full_details": f"Amazon Search: {query}"},
            )

        elif action == "search_flipkart":
            query = kwargs.get("query", "")
            if not query:
                return ToolResult(status="FAILED", message="What would you like to search on Flipkart?")
            import urllib.parse
            url = f"https://www.flipkart.com/search?q={urllib.parse.quote_plus(query)}"
            ChromeAdapter.open_url(url)
            return ToolResult(
                status="SUCCESS",
                message=f"Searching Flipkart for {query}.",
                data={"query": query, "url": url, "full_details": f"Flipkart Search: {query}"},
            )

        elif action == "search_github":
            query = kwargs.get("query", "")
            if not query:
                return ToolResult(status="FAILED", message="What would you like to search on GitHub?")
            import urllib.parse
            url = f"https://github.com/search?q={urllib.parse.quote_plus(query)}"
            ChromeAdapter.open_url(url)
            return ToolResult(
                status="SUCCESS",
                message=f"Searching GitHub for {query}.",
                data={"query": query, "url": url, "full_details": f"GitHub Search: {query}"},
            )

        elif action == "search_reddit":
            query = kwargs.get("query", "")
            if not query:
                return ToolResult(status="FAILED", message="What would you like to search on Reddit?")
            import urllib.parse
            url = f"https://www.reddit.com/search/?q={urllib.parse.quote_plus(query)}"
            ChromeAdapter.open_url(url)
            return ToolResult(
                status="SUCCESS",
                message=f"Searching Reddit for {query}.",
                data={"query": query, "url": url, "full_details": f"👽 Reddit Search: {query}"},
            )

        elif action == "search_wikipedia":
            query = kwargs.get("query", "")
            if not query:
                return ToolResult(status="FAILED", message="What would you like to search on Wikipedia?")
            import urllib.parse
            url = f"https://en.wikipedia.org/wiki/Special:Search?search={urllib.parse.quote_plus(query)}"
            ChromeAdapter.open_url(url)
            return ToolResult(
                status="SUCCESS",
                message=f"Searching Wikipedia for {query}.",
                data={"query": query, "url": url, "full_details": f"📖 Wikipedia Search: {query}"},
            )

        elif action == "open_url":
            url = kwargs.get("url", "")
            if not url.startswith("http://") and not url.startswith("https://"):
                url = f"https://{url}"
            ChromeAdapter.open_url(url)
            return ToolResult(
                status="SUCCESS",
                message=f"Opening {url}.",
                data={"url": url, "full_details": f"🌐 Navigating to: {url}"},
            )

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
