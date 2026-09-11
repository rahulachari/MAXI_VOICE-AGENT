"""
JARVIS Messaging & Communication Tool
Handles WhatsApp Desktop, Telegram, and Email composition via system automation.
"""

import os
import time
import subprocess
import webbrowser
import urllib.parse
import pyautogui
from .base import BaseTool, ToolResult


class MessagingTool(BaseTool):
    name = "MessagingTool"
    description = "Sends WhatsApp messages, Telegram messages, and composes emails."

    def execute(self, action: str, **kwargs) -> ToolResult:
        action = action.lower().strip()

        if action == "send_whatsapp":
            return self.send_whatsapp(kwargs.get("contact", ""), kwargs.get("message", ""))
        elif action == "send_telegram":
            return self.send_telegram(kwargs.get("contact", ""), kwargs.get("message", ""))
        elif action == "compose_email":
            return self.compose_email(
                kwargs.get("recipient", ""),
                kwargs.get("subject", ""),
                kwargs.get("body", ""),
            )
        elif action == "call_contact":
            return self.call_via_whatsapp(kwargs.get("contact", ""))

        return ToolResult(status="FAILED", message=f"Unknown messaging action: {action}")

    def send_whatsapp(self, contact: str, message: str = "") -> ToolResult:
        """Opens WhatsApp Desktop and searches for a contact. If message provided, types it."""
        if not contact:
            return ToolResult(status="FAILED", message="Which contact should I message on WhatsApp?")

        try:
            # Method 1: Try WhatsApp Desktop via Windows Start
            whatsapp_paths = [
                os.path.expandvars(r"%LOCALAPPDATA%\WhatsApp\WhatsApp.exe"),
                os.path.expandvars(r"%PROGRAMFILES%\WindowsApps\WhatsApp"),
            ]

            launched = False
            for path in whatsapp_paths:
                if os.path.exists(path):
                    subprocess.Popen([path], shell=True)
                    launched = True
                    break

            if not launched:
                # Fallback: try launching via start menu or shell
                try:
                    subprocess.Popen("start whatsapp:", shell=True)
                    launched = True
                except Exception:
                    pass

            if not launched:
                # Last resort: open WhatsApp Web
                webbrowser.open("https://web.whatsapp.com")
                time.sleep(2.0)
                return ToolResult(
                    status="SUCCESS",
                    message=f"Opened WhatsApp Web. Please search for {contact.title()} manually.",
                )

            time.sleep(2.5)

            # Search for the contact using Ctrl+F or the search bar
            pyautogui.hotkey("ctrl", "f")
            time.sleep(0.5)
            pyautogui.typewrite(contact, interval=0.03)
            time.sleep(1.5)
            pyautogui.press("enter")
            time.sleep(0.8)

            if message:
                from jarvis.utils.text_cleaner import clean_for_plain_text
                clean_msg = clean_for_plain_text(message, target="plain")
                pyautogui.typewrite(clean_msg, interval=0.02)
                # Don't auto-send: let the user review first
                return ToolResult(
                    status="SUCCESS",
                    message=f"Typed your message to {contact.title()} on WhatsApp. Press Enter to send.",
                )

            return ToolResult(
                status="SUCCESS",
                message=f"Opened {contact.title()}'s chat on WhatsApp. You can start typing your message.",
            )

        except Exception as e:
            return ToolResult(status="FAILED", message=f"Failed to open WhatsApp: {str(e)}")

    def send_telegram(self, contact: str, message: str = "") -> ToolResult:
        """Opens Telegram Desktop and searches for a contact."""
        if not contact:
            return ToolResult(status="FAILED", message="Which contact should I message on Telegram?")

        try:
            # Try opening Telegram Desktop
            try:
                subprocess.Popen("start telegram:", shell=True)
            except Exception:
                webbrowser.open("https://web.telegram.org")

            time.sleep(2.0)

            # Search for contact
            pyautogui.hotkey("ctrl", "k")  # Telegram search shortcut
            time.sleep(0.5)
            pyautogui.typewrite(contact, interval=0.03)
            time.sleep(1.0)
            pyautogui.press("enter")
            time.sleep(0.5)

            if message:
                from jarvis.utils.text_cleaner import clean_for_plain_text
                clean_msg = clean_for_plain_text(message, target="plain")
                pyautogui.typewrite(clean_msg, interval=0.02)
                return ToolResult(
                    status="SUCCESS",
                    message=f"Typed your message to {contact.title()} on Telegram. Press Enter to send.",
                )

            return ToolResult(
                status="SUCCESS",
                message=f"Opened {contact.title()}'s chat on Telegram.",
            )

        except Exception as e:
            return ToolResult(status="FAILED", message=f"Failed to open Telegram: {str(e)}")

    def compose_email(self, recipient: str = "", subject: str = "", body: str = "") -> ToolResult:
        """Opens Gmail compose in the browser with optional pre-filled fields."""
        try:
            from jarvis.utils.text_cleaner import clean_for_plain_text

            clean_subj = clean_for_plain_text(subject, target="plain") if subject else ""
            clean_body = clean_for_plain_text(body, target="email") if body else ""

            # Build Gmail compose URL
            params = {}
            if recipient:
                params["to"] = recipient.strip()
            if clean_subj:
                params["su"] = clean_subj
            if clean_body:
                params["body"] = clean_body

            if params:
                url = f"https://mail.google.com/mail/?view=cm&fs=1&{urllib.parse.urlencode(params)}"
            else:
                url = "https://mail.google.com/mail/?view=cm&fs=1"

            webbrowser.open(url)

            if recipient:
                return ToolResult(
                    status="SUCCESS",
                    message=f"Composing email to {recipient}." + (f" Subject: {subject}." if subject else ""),
                )
            return ToolResult(status="SUCCESS", message="Opened email compose window.")

        except Exception as e:
            return ToolResult(status="FAILED", message=f"Failed to open email: {str(e)}")

    def call_via_whatsapp(self, contact: str) -> ToolResult:
        """Attempts to initiate a WhatsApp call by opening the contact chat."""
        if not contact:
            return ToolResult(status="FAILED", message="Who would you like to call?")

        # Open the contact in WhatsApp first
        result = self.send_whatsapp(contact)
        if result.is_success():
            return ToolResult(
                status="SUCCESS",
                message=f"Opened {contact.title()}'s chat. You can start a voice or video call from there.",
            )
        return result
