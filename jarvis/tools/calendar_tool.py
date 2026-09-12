"""
JARVIS Calendar Tool
Opens Google Calendar with pre-filled event details from natural language.
Supports: "Schedule a meeting with X on Thursday at 2pm"
"""

import webbrowser
import urllib.parse
from datetime import datetime, timedelta
import re
from typing import Optional, Tuple
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

    def _clean_event_title(self, raw_title: str) -> tuple:
        """
        Strips platform names, dates, times, and filler commands from event title.
        Returns: (clean_title, extracted_date_dt, extracted_time_str)
        """
        if not raw_title:
            return "Important Meeting", None, ""

        now = datetime.now()
        text = raw_title.strip()
        extracted_date = None
        extracted_time = ""

        # 1. Extract explicit date if embedded in title (e.g., '14th september', 'october 25th', 'tomorrow')
        months_pat = r'(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)'
        m_d1 = re.search(r'\b(\d{1,2})(?:st|nd|rd|th)?\s+(' + months_pat + r')(?:\s+(\d{4}))?\b', text, re.I)
        m_d2 = re.search(r'\b(' + months_pat + r')\s+(\d{1,2})(?:st|nd|rd|th)?(?:\s+(\d{4}))?\b', text, re.I)

        if m_d1:
            day = int(m_d1.group(1))
            month_str = m_d1.group(2)[:3].capitalize()
            year = int(m_d1.group(3)) if m_d1.group(3) else now.year
            dt_str = f"{day} {month_str} {year}"
            try:
                extracted_date = datetime.strptime(dt_str, "%d %b %Y")
                if extracted_date.date() < now.date() and not m_d1.group(3):
                    extracted_date = extracted_date.replace(year=now.year + 1)
            except Exception:
                pass
        elif m_d2:
            month_str = m_d2.group(1)[:3].capitalize()
            day = int(m_d2.group(2))
            year = int(m_d2.group(3)) if m_d2.group(3) else now.year
            dt_str = f"{day} {month_str} {year}"
            try:
                extracted_date = datetime.strptime(dt_str, "%d %b %Y")
                if extracted_date.date() < now.date() and not m_d2.group(3):
                    extracted_date = extracted_date.replace(year=now.year + 1)
            except Exception:
                pass
        elif re.search(r'\bday\s+after\s+tomorrow\b', text, re.I):
            extracted_date = now + timedelta(days=2)
        elif re.search(r'\btomorrow\b', text, re.I):
            extracted_date = now + timedelta(days=1)

        # 2. Extract clock time if in title (e.g. 'at 9:00', 'at 3pm', 'for 10am')
        m_t = re.search(r'\b(?:at|for)\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\b', text, re.I)
        if m_t:
            extracted_time = m_t.group(1).strip()

        # 3. Strip platform references
        clean = re.sub(r'(?i)\b(?:on|in)?\s*(?:google\s+calendar|my\s+calendar|calendar)\b', '', text)
        # Strip dates
        clean = re.sub(r'(?i)\b(?:on|for)?\s*\d{1,2}(?:st|nd|rd|th)?\s+' + months_pat + r'(?:\s+\d{4})?\b', '', clean)
        clean = re.sub(r'(?i)\b(?:on|for)?\s*' + months_pat + r'\s+\d{1,2}(?:st|nd|rd|th)?(?:\s+\d{4})?\b', '', clean)
        clean = re.sub(r'(?i)\b(?:on|for)?\s*(?:today|tomorrow|day after tomorrow)\b', '', clean)
        # Strip times
        clean = re.sub(r'(?i)\b(?:at|for)\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?\b', '', clean)
        # Strip command prefixes & verbal fillers
        clean = re.sub(r'(?i)^(?:please\s+)?(?:open\s+(?:my\s+)?calendar\s+and\s+)?', '', clean)
        clean = re.sub(r'(?i)^(?:remind\s+me\s+(?:to\s+|that\s+|about\s+|for\s+)?|i\s+need\s+to\s+)', '', clean)
        clean = re.sub(r'(?i)^(?:set\s+(?:an?\s+)?|schedule\s+(?:an?\s+)?|mark\s+(?:the\s+)?(?:date\s+)?|marking\s+(?:the\s+)?(?:date\s+)?|add\s+(?:an?\s+)?|create\s+(?:an?\s+)?)', '', clean)
        clean = re.sub(r'(?i)^(?:event|reminder)\s+(?:for|about|on)?\s*', '', clean)
        clean = re.sub(r'(?i)^(?:on|for|at|about|to|that)\s+', '', clean)
        clean = re.sub(r'(?i)\s+(?:on|for|at|in)\s*$', '', clean)
        clean = re.sub(r'\s+', ' ', clean).strip()

        if not clean or clean.lower() in ["date", "time", "event", "calendar", "google calendar"]:
            clean = "Important Meeting"
        else:
            clean = clean.title()

        return clean, extracted_date, extracted_time

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
        """Opens Google Calendar with a pre-filled, sanitized event."""
        # Sanitize title and extract embedded dates/times
        clean_title, embedded_date, embedded_time = self._clean_event_title(title)

        # Parse date: prioritize explicit date_str, then embedded_date
        event_date = self._parse_date(date_str) if (date_str and date_str.lower() != "today") else embedded_date
        if not event_date and date_str:
            event_date = self._parse_date(date_str)

        # Parse time: prioritize explicit time_str, then embedded_time
        effective_time = time_str or embedded_time or "9:00 AM"
        event_time = self._parse_time(effective_time)

        now = datetime.now()
        if event_date and event_time:
            start_dt = event_date.replace(
                hour=event_time.hour, minute=event_time.minute, second=0
            )
        elif event_date:
            start_dt = event_date.replace(hour=9, minute=0, second=0)  # Default 9 AM
        elif event_time:
            start_dt = now.replace(
                hour=event_time.hour, minute=event_time.minute, second=0
            )
            if start_dt < now:
                start_dt += timedelta(days=1)
        else:
            # Default: tomorrow at 9 AM
            start_dt = (now + timedelta(days=1)).replace(
                hour=9, minute=0, second=0
            )

        end_dt = start_dt + timedelta(minutes=duration_min)

        # Format for Google Calendar URL
        start_fmt = start_dt.strftime("%Y%m%dT%H%M%S")
        end_fmt = end_dt.strftime("%Y%m%dT%H%M%S")

        params = {
            "action": "TEMPLATE",
            "text": clean_title,
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

        # Launch Windows Calendar / Outlook Calendar
        try:
            import subprocess
            subprocess.Popen(["cmd", "/c", "start", "outlookcal:"], shell=True)
        except Exception:
            pass

        # Save to local tasks database as an active scheduled reminder
        try:
            from jarvis.tools.task_tool import TaskTool
            task_tool = TaskTool()
            task_tool.add_task(title=clean_title, due_str=start_dt.strftime("%Y-%m-%d %H:%M:%S"))
        except Exception:
            pass

        time_display = start_dt.strftime("%I:%M %p").lstrip("0")
        if start_dt.date() == now.date():
            day_display = "today"
        elif start_dt.date() == (now + timedelta(days=1)).date():
            day_display = "tomorrow"
        else:
            day_display = f"for {start_dt.strftime('%A, %B %d')}"

        msg = f"I've opened your calendar and scheduled '{clean_title}' {day_display} at {time_display}."
        if attendees:
            msg += f" Added {attendees} as an attendee."

        return ToolResult(
            status="SUCCESS",
            message=msg,
            data={"url": url, "start": start_fmt, "end": end_fmt, "title": clean_title, "full_details": f"📅 Event: {clean_title}\n🕒 When: {start_dt.strftime('%A, %B %d, %Y at %I:%M %p')}\n🔗 Status: Scheduled in Google Calendar"},
        )

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parses natural language date like '14th September', 'Thursday', 'tomorrow', 'next Monday'."""
        if not date_str:
            return None

        text = date_str.lower().strip()
        now = datetime.now()

        if text == "today":
            return now
        elif text == "tomorrow":
            return now + timedelta(days=1)
        elif "day after tomorrow" in text:
            return now + timedelta(days=2)
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

        # Handle ordinal dates: '14th september', 'september 14th'
        months_pat = r'(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)'
        m_d1 = re.search(r'\b(\d{1,2})(?:st|nd|rd|th)?\s+(' + months_pat + r')(?:\s+(\d{4}))?\b', text, re.I)
        m_d2 = re.search(r'\b(' + months_pat + r')\s+(\d{1,2})(?:st|nd|rd|th)?(?:\s+(\d{4}))?\b', text, re.I)

        if m_d1:
            day = int(m_d1.group(1))
            month_str = m_d1.group(2)[:3].capitalize()
            year = int(m_d1.group(3)) if m_d1.group(3) else now.year
            try:
                dt = datetime.strptime(f"{day} {month_str} {year}", "%d %b %Y")
                if dt.date() < now.date() and not m_d1.group(3):
                    dt = dt.replace(year=now.year + 1)
                return dt
            except Exception:
                pass
        elif m_d2:
            month_str = m_d2.group(1)[:3].capitalize()
            day = int(m_d2.group(2))
            year = int(m_d2.group(3)) if m_d2.group(3) else now.year
            try:
                dt = datetime.strptime(f"{day} {month_str} {year}", "%d %b %Y")
                if dt.date() < now.date() and not m_d2.group(3):
                    dt = dt.replace(year=now.year + 1)
                return dt
            except Exception:
                pass

        # Clean ordinals for standard strptime
        clean_text = re.sub(r'(\d{1,2})(?:st|nd|rd|th)', r'\1', text)
        for fmt in ["%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%Y", "%B %d", "%b %d", "%d %B", "%d %b", "%B %d %Y", "%d %B %Y"]:
            try:
                parsed = datetime.strptime(clean_text, fmt)
                if parsed.year == 1900:
                    parsed = parsed.replace(year=now.year)
                    if parsed.date() < now.date():
                        parsed = parsed.replace(year=now.year + 1)
                return parsed
            except ValueError:
                continue

        return None

    def _parse_time(self, time_str: str) -> Optional[datetime]:
        """Parses natural time like '2pm', '14:30', '2:30 PM', '9:00 AM'."""
        if not time_str:
            return None

        text = time_str.lower().strip()

        # Handle "2pm", "2 pm", "14:30", "2:30 pm", "9:00"
        time_match = re.search(
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
            elif not period:
                # If unspecified and 1 <= hour <= 6, assume afternoon (e.g. 3 -> 15:00)
                if 1 <= hour <= 6:
                    hour += 12

            return datetime.now().replace(hour=hour, minute=minute, second=0)

        return None

