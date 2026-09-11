"""
JARVIS Weather & Time Tool
Provides real-time local and global weather forecasts via wttr.in and live system time.
"""

import json
import urllib.request
import urllib.parse
from datetime import datetime
from typing import Optional, Dict, Any
from .base import BaseTool, ToolResult


class WeatherTool(BaseTool):
    name = "WeatherTool"
    description = "Provides real-time live weather forecasts and accurate system time/date."

    def execute(self, action: str, **kwargs) -> ToolResult:
        action = (action or "").lower().strip()

        if action in ["get_weather", "weather", "forecast", "temperature"]:
            location = kwargs.get("location", kwargs.get("city", "")).strip()
            return self.get_weather(location)

        elif action in ["get_time", "time", "current_time"]:
            return self.get_time()

        elif action in ["get_date", "date", "today"]:
            return self.get_date()

        return self.get_weather(kwargs.get("location", ""))

    def get_weather(self, location: str = "") -> ToolResult:
        """Fetches live real-time weather from wttr.in."""
        clean_loc = location.strip()
        if clean_loc.lower() in ["here", "current", "my location", "local", "me", "today"]:
            clean_loc = ""

        # Format URL for wttr.in JSON
        encoded_loc = urllib.parse.quote(clean_loc) if clean_loc else ""
        url = f"https://wttr.in/{encoded_loc}?format=j1"

        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "curl/7.68.0", "Accept": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            curr = data.get("current_condition", [{}])[0]
            nearest = data.get("nearest_area", [{}])[0]

            city = clean_loc.capitalize() if clean_loc else ""
            if not city:
                area_names = nearest.get("areaName", [{}])
                city = area_names[0].get("value", "your area") if area_names else "your area"

            temp_c = curr.get("temp_C", "N/A")
            temp_f = curr.get("temp_F", "N/A")
            desc_list = curr.get("weatherDesc", [{}])
            desc = desc_list[0].get("value", "clear skies") if desc_list else "clear skies"
            humidity = curr.get("humidity", "N/A")
            feels_like_c = curr.get("FeelsLikeC", temp_c)
            wind_kmph = curr.get("windspeedKmph", "N/A")

            spoken_message = (
                f"Currently in {city}, it is {temp_c}°C with {desc.lower()}. "
                f"It feels like {feels_like_c}°C with {humidity}% humidity."
            )

            full_details = (
                f"🌤️ Live Weather: {city}\n"
                f"• Temperature: {temp_c}°C ({temp_f}°F)\n"
                f"• Condition: {desc}\n"
                f"• Feels Like: {feels_like_c}°C\n"
                f"• Humidity: {humidity}%\n"
                f"• Wind Speed: {wind_kmph} km/h"
            )

            return ToolResult(
                status="SUCCESS",
                message=spoken_message,
                data={
                    "city": city,
                    "temp_c": temp_c,
                    "temp_f": temp_f,
                    "condition": desc,
                    "humidity": humidity,
                    "feels_like_c": feels_like_c,
                    "full_details": full_details,
                },
            )

        except Exception as e:
            now_time = datetime.now().strftime("%I:%M %p")
            fallback_msg = f"I couldn't reach the live weather service right now, but the current local time is {now_time}."
            return ToolResult(
                status="FAILED",
                message=fallback_msg,
                error=str(e),
                data={"full_details": f"Weather Service Unavailable: {e}"},
            )

    def get_time(self) -> ToolResult:
        """Returns live system time with natural speech formatting."""
        now = datetime.now()
        time_str = now.strftime("%I:%M %p").lstrip("0")
        day_str = now.strftime("%A")
        date_str = now.strftime("%B %d, %Y")

        spoken = f"It is currently {time_str} on {day_str}."
        full_details = f"🕒 Current Time: {time_str}\n📅 Date: {day_str}, {date_str}"

        return ToolResult(
            status="SUCCESS",
            message=spoken,
            data={"time": time_str, "day": day_str, "date": date_str, "full_details": full_details},
        )

    def get_date(self) -> ToolResult:
        """Returns today's date."""
        now = datetime.now()
        date_str = now.strftime("%A, %B %d, %Y")
        spoken = f"Today is {date_str}."
        return ToolResult(
            status="SUCCESS",
            message=spoken,
            data={"date": date_str, "full_details": f"📅 Today's Date: {date_str}"},
        )
