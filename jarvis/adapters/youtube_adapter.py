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

    @classmethod
    def get_direct_play_url(cls, query: str) -> str:
        """Finds top matching YouTube video and returns direct playable watch URL."""
        import urllib.request
        import re

        clean_query = urllib.parse.quote_plus(query.strip())
        search_url = f"{cls.SEARCH_URL}{clean_query}"

        try:
            req = urllib.request.Request(
                search_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
            )
            with urllib.request.urlopen(req, timeout=4) as resp:
                html = resp.read().decode("utf-8", errors="ignore")

            video_ids = re.findall(r"/watch\?v=([a-zA-Z0-9_-]{11})", html)
            if video_ids:
                # First matching video ID
                return f"{cls.BASE_URL}/watch?v={video_ids[0]}&autoplay=1"
        except Exception as e:
            print(f"[YouTubeAdapter] Failed to fetch top video: {e}")

        # Fallback to search results if fetch failed
        return search_url
