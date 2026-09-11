"""
JARVIS Calendar Tool
Opens Google Calendar with pre-filled event details from natural language.
Supports: "Schedule a meeting with X on Thursday at 2pm"
"""

import webbrowser
import urllib.parse
from datetime import datetime, timedelta
import re
from .base import BaseTool, ToolResult


# Day name to next occurrence
DAY_NAMES = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6,
    "mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6,
}


class CalendarTool(BaseTool):
    name = "CalendarTool"
    description = "Creates Google Calendar events from voice commands."

    def execute(self, action: str, **kwargs) -> ToolResult:
        action = action.lower().strip()

        if action == "create_event":
            return self.create_event(
                title=kwargs.get("title", ""),
                date_str=kwargs.get("date", ""),
                time_str=kwargs.get("time", ""),
                duration_min=kwargs.get("duration", 30),
                attendees=kwargs.get("attendees", ""),
                location=kwargs.get("location", ""),
                description=kwargs.get("description", ""),
            )
        elif action == "open_calendar":
            webbrowser.open("https://calendar.google.com")
            return ToolResult(status="SUCCESS", message="Google Calendar is open.")

        return ToolResult(status="FAILED", message=f"Unknown calendar action: {action}")

    def create_event(
        self,
        title: str = "",
        date_str: str = "",
        time_str: str = "",
        duration_min: int = 30,
        attendees: str = "",
        location: str = "",
        description: str = "",
    ) -> ToolResult:
        """Opens Google Calendar with a pre-filled new event."""
        if not title:
            title = "New Event"

        # Parse date
        event_date = self._parse_date(date_str)
        event_time = self._parse_time(time_str)

        if event_date and event_time:
            start_dt = event_date.replace(
                hour=event_time.hour, minute=event_time.minute
            )
        elif event_date:
            start_dt = event_date.replace(hour=10, minute=0)  # Default 10 AM
        elif event_time:
            start_dt = datetime.now().replace(
                hour=event_time.hour, minute=event_time.minute, second=0
            )
            if start_dt < datetime.now():
                start_dt += timedelta(days=1)
        else:
            # Default: tomorrow at 10 AM
            start_dt = (datetime.now() + timedelta(days=1)).replace(
                hour=10, minute=0, second=0
            )

        end_dt = start_dt + timedelta(minutes=duration_min)

        # Format for Google Calendar URL
        start_fmt = start_dt.strftime("%Y%m%dT%H%M%S")
        end_fmt = end_dt.strftime("%Y%m%dT%H%M%S")

        params = {
            "action": "TEMPLATE",
            "text": title,
            "dates": f"{start_fmt}/{end_fmt}",
        }

        if attendees:
            params["add"] = attendees
        if location:
            params["location"] = location
        if description:
            params["details"] = description

        url = f"https://calendar.google.com/calendar/render?{urllib.parse.urlencode(params)}"
        webbrowser.open(url)

        time_display = start_dt.strftime("%A at %I:%M %p")
        msg = f"Creating event '{title}' on {time_display}."
        if attendees:
            msg += f" I've added {attendees} as an attendee."

        return ToolResult(
            status="SUCCESS",
            message=msg,
            data={"url": url, "start": start_fmt, "end": end_fmt},
        )

    def _parse_date(self, date_str: str) -> datetime:
        """Parses natural language date like 'Thursday', 'tomorrow', 'next Monday'."""
        if not date_str:
            return None

        text = date_str.lower().strip()
        now = datetime.now()

        if text == "today":
            return now
        elif text == "tomorrow":
            return now + timedelta(days=1)
        elif text.startswith("next "):
            day_name = text.replace("next ", "").strip()
            if day_name in DAY_NAMES:
                target_day = DAY_NAMES[day_name]
                days_ahead = (target_day - now.weekday() + 7) % 7
                if days_ahead == 0:
                    days_ahead = 7
                return now + timedelta(days=days_ahead)
        elif text in DAY_NAMES:
            target_day = DAY_NAMES[text]
            days_ahead = (target_day - now.weekday() + 7) % 7
            if days_ahead == 0:
                days_ahead = 7
            return now + timedelta(days=days_ahead)

        # Try explicit date format
        for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%B %d", "%b %d"]:
            try:
                parsed = datetime.strptime(text, fmt)
                if parsed.year == 1900:
                    parsed = parsed.replace(year=now.year)
                return parsed
            except ValueError:
                continue

        return None

    def _parse_time(self, time_str: str) -> datetime:
        """Parses natural time like '2pm', '14:30', '2:30 PM'."""
        if not time_str:
            return None

        text = time_str.lower().strip()

        # Handle "2pm", "2 pm", "14:30", "2:30 pm"
        time_match = re.match(
            r"(\d{1,2})(?::(\d{2}))?\s*(am|pm|a\.m\.|p\.m\.)?", text
        )
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2) or 0)
            period = time_match.group(3)

            if period and ("pm" in period or "p.m." in period):
                if hour < 12:
                    hour += 12
            elif period and ("am" in period or "a.m." in period):
                if hour == 12:
                    hour = 0

            return datetime.now().replace(hour=hour, minute=minute, second=0)

        return None
