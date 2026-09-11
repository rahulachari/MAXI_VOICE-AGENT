"""
JARVIS YouTube Adapter
Semantic URLs, search formatting, and video control helpers for YouTube.
"""

import urllib.parse


class YouTubeAdapter:
    BASE_URL = "https://www.youtube.com"
    SEARCH_URL = "https://www.youtube.com/results?search_query="

    @classmethod
    def get_home_url(cls) -> str:
        return cls.BASE_URL

    @classmethod
    def get_search_url(cls, query: str) -> str:
        clean_query = urllib.parse.quote_plus(query.strip())
        return f"{cls.SEARCH_URL}{clean_query}"
