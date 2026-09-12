"""
JARVIS Weather & Time Tool
Provides real-time local and global weather forecasts via wttr.in and live system time.
"""

import re
import json
import urllib.request
import urllib.parse
from datetime import datetime
from typing import Optional, Dict, Any
from .base import BaseTool, ToolResult
from jarvis.app.config import config


class WeatherTool(BaseTool):
    name = "WeatherTool"
    description = "Provides real-time live weather forecasts and accurate system time/date."

    def execute(self, action: str, **kwargs) -> ToolResult:
        action = (action or "").lower().strip()

        if action in ["get_weather", "weather", "forecast", "temperature", "live_report"]:
            location = (
                kwargs.get("location")
                or kwargs.get("city")
                or kwargs.get("query")
                or kwargs.get("target")
                or ""
            ).strip()
            return self.get_weather(location)

        elif action in ["get_time", "time", "current_time"]:
            return self.get_time()

        elif action in ["get_date", "date", "today"]:
            return self.get_date()

        loc = kwargs.get("location") or kwargs.get("city") or kwargs.get("query") or ""
        return self.get_weather(loc)

    def get_weather(self, location: str = "") -> ToolResult:
        """Fetches live real-time weather and meteorological reports via OpenWeatherMap or live satellite."""
        clean_loc = (location or "").strip()
        # Clean phrases like "what's the weather in", "weather report for", etc.
        clean_loc = re.sub(
            r"(?i)(what\'?s\s+the\s+weather\s+(in|of|at)|weather\s+report\s+(for|in|of)|weather\s+(in|of|at)|forecast\s+(for|in)|temperature\s+(in|of)|live\s+weather\s+(for|in)|in\s+|at\s+)",
            "",
            clean_loc,
        ).strip()
        clean_loc = clean_loc.rstrip("?.,!").strip()

        if clean_loc.lower() in ["here", "current", "my location", "local", "me", "today"]:
            clean_loc = ""

        # Default to user's home city (e.g. Chittoor) instead of ISP's gateway IP
        if not clean_loc:
            clean_loc = str(config.get("default_city", "Chittoor")).strip() or "Chittoor"

        encoded_loc = urllib.parse.quote(clean_loc)

        # 1. Check if OpenWeatherMap API key is provided
        weather_key = str(config.get("weather_api_key", "")).strip()
        if weather_key and clean_loc:
            try:
                owm_url = f"https://api.openweathermap.org/data/2.5/weather?q={encoded_loc}&appid={weather_key}&units=metric"
                req = urllib.request.Request(owm_url, headers={"Accept": "application/json"})
                with urllib.request.urlopen(req, timeout=5) as resp:
                    owm_data = json.loads(resp.read().decode("utf-8"))

                city = owm_data.get("name", clean_loc.capitalize())
                main = owm_data.get("main", {})
                temp_c = round(main.get("temp", 0))
                feels_like_c = round(main.get("feels_like", temp_c))
                max_temp = round(main.get("temp_max", temp_c))
                min_temp = round(main.get("temp_min", temp_c))
                humidity = main.get("humidity", 0)
                wind = owm_data.get("wind", {})
                wind_kmph = round(wind.get("speed", 0) * 3.6)
                weather_desc = owm_data.get("weather", [{}])[0].get("description", "clear skies")

                spoken_message = (
                    f"Currently in {city}, it is {temp_c}°C with {weather_desc}. "
                    f"Today expect a high of {max_temp}°C and a low of {min_temp}°C with {humidity}% humidity."
                )
                full_details = (
                    f"Live Weather Report for {city}: Currently {temp_c}°C with {weather_desc} (feels like {feels_like_c}°C). "
                    f"Today's forecast reaches a high of {max_temp}°C and a low of {min_temp}°C. "
                    f"Humidity is {humidity}% with wind speed at {wind_kmph} km/h."
                )
                return ToolResult(
                    status="SUCCESS",
                    message=spoken_message,
                    data={
                        "city": city,
                        "temp_c": temp_c,
                        "condition": weather_desc,
                        "humidity": humidity,
                        "feels_like_c": feels_like_c,
                        "full_details": full_details,
                        "source": "OpenWeatherMap",
                    },
                )
            except Exception as e:
                print(f"[WeatherTool] OpenWeatherMap failed, using live satellite: {e}")

        # 2. Comprehensive Live Weather & Forecast via global meteorological network (zero-key required)
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
            today_weather = data.get("weather", [{}])[0] if data.get("weather") else {}
            hourly = today_weather.get("hourly", [{}])

            city = clean_loc.capitalize() if clean_loc else ""
            if not city:
                area_names = nearest.get("areaName", [{}])
                city = area_names[0].get("value", "your area") if area_names else "your area"

            temp_c = curr.get("temp_C", "N/A")
            desc_list = curr.get("weatherDesc", [{}])
            desc = desc_list[0].get("value", "clear skies").strip() if desc_list else "clear skies"
            humidity = curr.get("humidity", "N/A")
            feels_like_c = curr.get("FeelsLikeC", temp_c)
            wind_kmph = curr.get("windspeedKmph", "N/A")
            wind_dir = curr.get("winddir16Point", "")
            uv = today_weather.get("uvIndex", curr.get("uvIndex", "N/A"))
            max_temp = today_weather.get("maxtempC", temp_c)
            min_temp = today_weather.get("mintempC", temp_c)

            spoken_message = (
                f"Currently in {city}, it is {temp_c}°C with {desc.lower()}. "
                f"Today expect a high of {max_temp}°C and low of {min_temp}°C with {humidity}% humidity."
            )

            full_details = (
                f"Live Weather Report for {city}: Currently {temp_c}°C with {desc.lower()} (feels like {feels_like_c}°C). "
                f"Today's forecast reaches a high of {max_temp}°C and a low of {min_temp}°C. "
                f"Humidity is {humidity}%, wind speed {wind_kmph} km/h from {wind_dir}, and UV index is {uv}."
            )

            return ToolResult(
                status="SUCCESS",
                message=spoken_message,
                data={
                    "city": city,
                    "temp_c": temp_c,
                    "max_temp": max_temp,
                    "min_temp": min_temp,
                    "condition": desc,
                    "humidity": humidity,
                    "feels_like_c": feels_like_c,
                    "wind_kmph": wind_kmph,
                    "wind_dir": wind_dir,
                    "uv_index": uv,
                    "full_details": full_details,
                    "source": "Live Meteorological Satellite",
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
