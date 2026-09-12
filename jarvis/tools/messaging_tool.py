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
        elif action == "share_file_whatsapp":
            return self.share_file_whatsapp(kwargs.get("contact", ""))
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

    def share_file_whatsapp(self, contact: str = "") -> ToolResult:
        """Shares the last opened file via WhatsApp Desktop"""
        last_file = os.environ.get("JARVIS_LAST_FILE", "")
        if not last_file or not os.path.exists(last_file):
            return ToolResult(status="FAILED", message="I don't remember which file you opened recently. Please open it first.")

        try:
            # Copy file to clipboard
            subprocess.run(["powershell", "-command", f"Set-Clipboard -Path '{last_file}'"])
            time.sleep(0.5)

            # Open WhatsApp
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
                subprocess.Popen("start whatsapp:", shell=True)
            
            time.sleep(2.5)

            if contact:
                # Search contact
                pyautogui.hotkey("ctrl", "f")
                time.sleep(0.5)
                pyautogui.typewrite(contact, interval=0.03)
                time.sleep(1.5)
                pyautogui.press("enter")
                time.sleep(1.0)
                
                # Paste file
                pyautogui.hotkey("ctrl", "v")
                time.sleep(1.0)
                pyautogui.press("enter")
                
                return ToolResult(
                    status="SUCCESS",
                    message=f"Shared the file with {contact.title()} on WhatsApp.",
                )
            else:
                return ToolResult(
                    status="SUCCESS",
                    message="Opened WhatsApp. Please select a contact and press Ctrl+V to paste the file.",
                )
        except Exception as e:
            return ToolResult(status="FAILED", message=f"Failed to share file on WhatsApp: {str(e)}")

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

        # Open the contact in WhatsApp first (this will search and focus the chat)
        result = self.send_whatsapp(contact)
        if result.is_success():
            # Wait for the chat to fully load
            time.sleep(1.0)
            
            # Use WhatsApp Desktop shortcut for voice call (Ctrl + Alt + C)
            pyautogui.hotkey("ctrl", "alt", "c")
            time.sleep(0.5)
            
            return ToolResult(
                status="SUCCESS",
                message=f"Placing a call to {contact.title()} on WhatsApp.",
            )
        return result
