"""
JARVIS Email Reader Tool
Reads recent emails from Gmail via secure IMAP or opens webmail,
providing spoken summaries and in-notch visual email cards.
"""

import os
import email
from email.header import decode_header
import imaplib
import webbrowser
from typing import List, Dict, Any, Optional
from .base import BaseTool, ToolResult
from jarvis.app.config import config
from jarvis.utils.text_cleaner import clean_spoken_text, clean_for_plain_text


def _clean_header_str(val: Any) -> str:
    if not val:
        return ""
    try:
        decoded_parts = decode_header(val)
        result = []
        for part, enc in decoded_parts:
            if isinstance(part, bytes):
                result.append(part.decode(enc or "utf-8", errors="ignore"))
            else:
                result.append(str(part))
        return " ".join(result).strip()
    except Exception:
        return str(val)


class EmailReaderTool(BaseTool):
    name = "EmailReaderTool"
    description = "Fetches and summarizes recent Gmail inbox messages."

    def execute(self, action: str, **kwargs) -> ToolResult:
        action = action.lower().strip()
        if action in ["read_emails", "check_emails", "check_gmail", "read_inbox", "read_gmail"]:
            return self.read_recent_emails()
        return ToolResult(status="FAILED", message=f"Unknown email action: {action}")

    def read_recent_emails(self, limit: int = 5) -> ToolResult:
        username = config.get("gmail_user") or os.getenv("GMAIL_USER", "")
        password = config.get("gmail_app_password") or os.getenv("GMAIL_APP_PASSWORD", "")

        # If not configured, open Gmail in browser and guide user
        if not username or not password:
            webbrowser.open("https://mail.google.com")
            msg = (
                "I opened your Gmail inbox in your browser. "
                "To have me read your unread emails out loud inside the notch, "
                "please enter your Gmail and App Password in Settings."
            )
            return ToolResult(
                status="SUCCESS",
                message=msg,
                data={
                    "is_email_list": True,
                    "emails": [
                        {
                            "sender": "Gmail Webmail",
                            "subject": "Inbox opened in your browser. Add GMAIL_USER & GMAIL_APP_PASSWORD to .env to read emails inside the notch.",
                            "date": "Now",
                        }
                    ],
                    "url": "https://mail.google.com",
                    "full_details": "Gmail opened in browser. To enable in-notch audio reading, configure your Gmail in Settings.",
                },
            )

        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(username, password)
            mail.select("INBOX")

            # Search unread first, fallback to all recent
            status, response = mail.search(None, "UNSEEN")
            email_ids = response[0].split()
            is_unread = True

            if not email_ids:
                status, response = mail.search(None, "ALL")
                email_ids = response[0].split()
                is_unread = False

            if not email_ids:
                mail.logout()
                return ToolResult(
                    status="SUCCESS",
                    message="Your Gmail inbox is completely empty right now.",
                    data={"emails": [], "full_details": "No emails found in inbox."},
                )

            # Get the most recent IDs
            recent_ids = email_ids[-limit:]
            recent_ids.reverse()

            emails_data: List[Dict[str, str]] = []

            for eid in recent_ids:
                status, msg_data = mail.fetch(eid, "(RFC822.HEADER)")
                if status != "OK":
                    continue
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        from_hdr = _clean_header_str(msg.get("From", "Unknown Sender"))
                        # Clean sender name: e.g. "John Doe <john@gmail.com>" -> "John Doe"
                        sender_clean = from_hdr.split("<")[0].replace('"', '').strip()
                        subject_clean = _clean_header_str(msg.get("Subject", "(No Subject)"))
                        date_str = msg.get("Date", "")[:16]

                        emails_data.append({
                            "sender": sender_clean or from_hdr,
                            "subject": subject_clean,
                            "date": date_str,
                        })

            mail.logout()

            count = len(emails_data)
            type_str = "unread" if is_unread else "recent"

            # Build clean spoken summary
            spoken_parts = [f"You have {count} {type_str} emails."]
            for idx, em in enumerate(emails_data[:3], 1):
                spoken_parts.append(f"From {em['sender']}: '{em['subject']}'.")

            spoken_summary = " ".join(spoken_parts)
            full_text = "\n".join(f"• {e['sender']}: {e['subject']} ({e['date']})" for e in emails_data)

            return ToolResult(
                status="SUCCESS",
                message=spoken_summary,
                data={
                    "is_email_list": True,
                    "emails": emails_data,
                    "full_details": full_text,
                },
            )

        except Exception as e:
            err_str = str(e)
            print(f"[EmailReader] IMAP error: {err_str}")
            webbrowser.open("https://mail.google.com")
            return ToolResult(
                status="SUCCESS",
                message="I couldn't connect to Gmail directly, so I opened your inbox in your browser.",
                data={"url": "https://mail.google.com", "full_details": f"Gmail opened in browser. Connection note: {err_str}"},
            )
