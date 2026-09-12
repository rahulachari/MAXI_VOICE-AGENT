"""
JARVIS Local Semantic Engine
100% offline rule-based semantic parser for core Windows, desktop, browser,
messaging (WhatsApp, email), media, and productivity commands.
"""

import re
from datetime import datetime
from typing import Optional
from .intent import Intent, IntentCategory
from .context import context_engine

POPULAR_SITES = {
    "google": "https://www.google.com",
    "youtube": "https://www.youtube.com",
    "reddit": "https://www.reddit.com",
    "github": "https://www.github.com",
    "twitter": "https://x.com",
    "x": "https://x.com",
    "chatgpt": "https://chatgpt.com",
    "chat gpt": "https://chatgpt.com",
    "gmail": "https://mail.google.com",
    "linkedin": "https://www.linkedin.com",
    "linked in": "https://www.linkedin.com",
    "linked-in": "https://www.linkedin.com",
    "spotify": "https://open.spotify.com",
    "instagram": "https://www.instagram.com",
    "facebook": "https://www.facebook.com",
    "amazon": "https://www.amazon.in",
    "flipkart": "https://www.flipkart.com",
    "netflix": "https://www.netflix.com",
    "whatsapp web": "https://web.whatsapp.com",
    "telegram": "https://web.telegram.org",
    "discord": "https://discord.com/app",
    "slack": "https://app.slack.com",
    "notion": "https://www.notion.so",
    "figma": "https://www.figma.com",
    "canva": "https://www.canva.com",
    "wikipedia": "https://en.wikipedia.org",
    "stack overflow": "https://stackoverflow.com",
    "stackoverflow": "https://stackoverflow.com",
    "portfolio": "https://rahulachariportfolio.vercel.app/",
    "my portfolio": "https://rahulachariportfolio.vercel.app/",
    "propcast": "https://propcast-oyan.onrender.com",
    "prop cast": "https://propcast-oyan.onrender.com",
    "uniml": "https://uniml.onrender.com",
    "uni ml": "https://uniml.onrender.com",
    "controld": "https://controld-three.vercel.app/login",
    "control d": "https://controld-three.vercel.app/login",
    "control-d": "https://controld-three.vercel.app/login",
}


class LocalSemanticEngine:
    @staticmethod
    def parse(transcript: str) -> Optional[Intent]:
        text = transcript.lower().strip()
        # Clean mid-speech pauses/punctuation inserted by STT without destroying filenames or URLs
        text = re.sub(r"[,?!]", " ", text)
        text = re.sub(r"(?<!\w)\.|\.(?!\w)", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        # Remove common politeness prefixes and wake words
        text = re.sub(r"^(jarvis|please|can you|could you|would you|hey jarvis|hi jarvis|ok jarvis)\s+", "", text).strip()

        # ===================================================================
        # 1. System Control
        # ===================================================================
        if text in ["stop", "cancel", "abort", "never mind", "quit", "pause", "shut up", "be quiet", "enough"]:
            return Intent(category=IntentCategory.CANCEL, action="cancel")

        # ===================================================================
        # 1.1. User Portfolio & Projects Navigation
        # ===================================================================
        if re.search(r"\b(?:open|launch|show|go to)\s+(?:my\s+)?portfolio\b", text):
            return Intent(category=IntentCategory.WEB_NAVIGATION, target="Portfolio", action="open_url", params={"url": "https://rahulachariportfolio.vercel.app/"})

        if re.search(r"\b(?:open|launch|go to)\s+(?:my\s+)?prop\s*cast(?:\s+live|\s+app)?\b", text):
            if "github" in text:
                return Intent(category=IntentCategory.WEB_NAVIGATION, target="PropCast GitHub", action="open_url", params={"url": "https://github.com/rahulachari/PropCast"})
            return Intent(category=IntentCategory.WEB_NAVIGATION, target="PropCast", action="open_url", params={"url": "https://propcast-oyan.onrender.com"})

        if re.search(r"\b(?:open|launch|go to)\s+(?:my\s+)?uni\s*ml(?:\s+live|\s+app)?\b", text):
            if "github" in text:
                return Intent(category=IntentCategory.WEB_NAVIGATION, target="UniML GitHub", action="open_url", params={"url": "https://github.com/rahulachari/UniML"})
            return Intent(category=IntentCategory.WEB_NAVIGATION, target="UniML", action="open_url", params={"url": "https://uniml.onrender.com"})

        if re.search(r"\b(?:open|launch|go to)\s+(?:my\s+)?control\s*[- ]?d(?:\s+live|\s+app)?\b", text):
            if "github" in text:
                return Intent(category=IntentCategory.WEB_NAVIGATION, target="ControL-D GitHub", action="open_url", params={"url": "https://github.com/rahulachari/ControL-D"})
            return Intent(category=IntentCategory.WEB_NAVIGATION, target="ControL-D", action="open_url", params={"url": "https://controld-three.vercel.app/login"})

        if re.search(r"\b(?:open|show|go to)\s+my\s+github\b", text):
            return Intent(category=IntentCategory.WEB_NAVIGATION, target="GitHub", action="open_url", params={"url": "https://github.com/rahulachari"})

        if re.search(r"\b(?:open|show|go to)\s+my\s+linkedin\b", text):
            return Intent(category=IntentCategory.WEB_NAVIGATION, target="LinkedIn", action="open_url", params={"url": "https://www.linkedin.com/in/rahulyc/"})

        # ===================================================================
        # 1.2. Autonomous Job Application & Resume Autofill / Paste
        # ===================================================================
        if re.search(r"\b(?:paste\s+(?:my\s+|the\s+)?resume|paste\s+resume\s+here)\b", text):
            return Intent(category=IntentCategory.JOB_APPLICATION, target="JobAgent", action="paste_resume", params={})

        if re.search(r"\b(?:apply\s+(?:for|to)\s+(?:this|the|a)?\s*job|apply\s+for\s+this|apply\s+now|autofill\s+job|fill\s+application)\b", text):
            return Intent(category=IntentCategory.JOB_APPLICATION, target="JobAgent", action="apply_for_job", params={})

        if re.search(r"\b(?:what\s+is\s+my\s+resume|show\s+my\s+resume|view\s+my\s+resume|check\s+my\s+resume|my\s+resume\s+details)\b", text):
            return Intent(category=IntentCategory.JOB_APPLICATION, target="JobAgent", action="get_profile", params={})

        # ===================================================================
        # 1.3. Universal Web & Multi-Platform Search (High Priority)
        # Guarantees commands like "search for iPhone 18 Pro", "google...",
        # "look up...", "search amazon for..." are IMMEDIATELY routed to search,
        # never colliding with calls or messaging.
        # ===================================================================

        # Explicit YouTube search: "search for [query] on youtube", "search youtube for [query]"
        if "youtube" in text and ("search" in text or text.startswith("play ")):
            yt_m = re.search(r"^(?:search\s+(?:on\s+)?youtube\s+for|search\s+for\s+(.+?)\s+on\s+youtube|search\s+(.+?)\s+on\s+youtube|youtube\s+search\s+(?:for\s+)?)(.+)$", text, re.IGNORECASE)
            q = ""
            if yt_m:
                q = (yt_m.group(1) or yt_m.group(2) or yt_m.group(3) or "").strip()
            elif "search" in text:
                q = text.replace("search for", "").replace("search", "").replace("on youtube", "").replace("youtube", "").strip()
            if q and q != "youtube":
                return Intent(category=IntentCategory.WEB_SEARCH, target="YouTube", action="search_youtube", params={"query": q})

        # Explicit Amazon search: "search for iphone 18 pro on amazon", "buy ... on amazon", "search amazon for ..."
        if "amazon" in text and ("search" in text or "buy" in text or "price" in text or "find" in text or "look" in text):
            q = re.sub(r"^(?:search\s+(?:on\s+)?amazon\s+for|search\s+amazon\s+for|search\s+for|search|buy|find|look\s+up)\s+", "", text, flags=re.IGNORECASE)
            q = re.sub(r"\s+on\s+amazon$", "", q, flags=re.IGNORECASE).strip()
            if q and q != "amazon":
                return Intent(category=IntentCategory.WEB_SEARCH, target="Amazon", action="search_amazon", params={"query": q})

        # Explicit Flipkart search: "search for iphone 18 pro on flipkart", "search flipkart for ..."
        if "flipkart" in text and ("search" in text or "buy" in text or "price" in text or "find" in text):
            q = re.sub(r"^(?:search\s+(?:on\s+)?flipkart\s+for|search\s+flipkart\s+for|search\s+for|search|buy|find)\s+", "", text, flags=re.IGNORECASE)
            q = re.sub(r"\s+on\s+flipkart$", "", q, flags=re.IGNORECASE).strip()
            if q and q != "flipkart":
                return Intent(category=IntentCategory.WEB_SEARCH, target="Flipkart", action="search_flipkart", params={"query": q})

        # Explicit GitHub search: "search github for ...", "search for ... on github"
        if "github" in text and "search" in text:
            q = re.sub(r"^(?:search\s+(?:on\s+)?github\s+for|search\s+github\s+for|search\s+for|search)\s+", "", text, flags=re.IGNORECASE)
            q = re.sub(r"\s+on\s+github$", "", q, flags=re.IGNORECASE).strip()
            if q and q != "github":
                return Intent(category=IntentCategory.WEB_SEARCH, target="GitHub", action="search_github", params={"query": q})

        # Explicit Reddit search: "search reddit for ...", "search for ... on reddit"
        if "reddit" in text and "search" in text:
            q = re.sub(r"^(?:search\s+(?:on\s+)?reddit\s+for|search\s+reddit\s+for|search\s+for|search)\s+", "", text, flags=re.IGNORECASE)
            q = re.sub(r"\s+on\s+reddit$", "", q, flags=re.IGNORECASE).strip()
            if q and q != "reddit":
                return Intent(category=IntentCategory.WEB_SEARCH, target="Reddit", action="search_reddit", params={"query": q})

        # Explicit Wikipedia search: "search wikipedia for ...", "search for ... on wikipedia"
        if "wikipedia" in text and "search" in text:
            q = re.sub(r"^(?:search\s+(?:on\s+)?wikipedia\s+for|search\s+wikipedia\s+for|search\s+for|search)\s+", "", text, flags=re.IGNORECASE)
            q = re.sub(r"\s+on\s+wikipedia$", "", q, flags=re.IGNORECASE).strip()
            if q and q != "wikipedia":
                return Intent(category=IntentCategory.WEB_SEARCH, target="Wikipedia", action="search_wikipedia", params={"query": q})

        # Universal Web / Google Search:
        # Handles:
        # - "search for iphone 18 pro"
        # - "search for the iphone 18 pro"
        # - "search for quantum computing"
        # - "search google for quantum computing"
        # - "google iphone 18 pro"
        # - "search web for latest AI news"
        # - "search the web for ..."
        # - "look up iphone 18 pro"
        # - "lookup iphone 18 pro specs"
        # - "search [anything]" (except local file queries)
        web_search_pattern = r"^(?:search\s+(?:google\s+for|on\s+google\s+for|the\s+web\s+for|web\s+for|internet\s+for|the\s+internet\s+for|for\s+(?:the\s+)?|for\s+|online\s+for\s+)|google\s+|look\s+up\s+|lookup\s+|browse\s+for\s+|search\s+)(.+)$"
        web_search_match = re.search(web_search_pattern, text, re.IGNORECASE)
        if web_search_match:
            q = web_search_match.group(1).strip()
            # Clean trailing search terms
            q = re.sub(r"\s+(?:on|in)\s+google$", "", q, flags=re.IGNORECASE).strip()
            # Guard against local file search commands: "search for file test.py" or "search for folder notes"
            if not q.startswith("file ") and not q.startswith("folder ") and q != "file" and q != "folder":
                return Intent(category=IntentCategory.WEB_SEARCH, target="Google", action="search_google", params={"query": q})

        # 2. Greetings and Identity
        if text in ["hello", "hi", "hey", "good morning", "good evening", "good afternoon", "how are you", "what's up", "hey there"]:
            return Intent(
                category=IntentCategory.AI_QUERY,
                action="query",
                params={"query": transcript},
                confirmation_prompt="Hello! I am JARVIS, ready to assist you.",
            )

        if text in ["who are you", "what is your name", "introduce yourself", "what are you", "what can you do"]:
            return Intent(
                category=IntentCategory.AI_QUERY,
                action="query",
                params={"query": transcript},
                confirmation_prompt="I am JARVIS, your desktop voice operating system assistant. I can open apps, search the web, send messages, write emails, control your system, and much more.",
            )

        # 3. System Time, Date & Weather
        if re.search(r"\b(?:what(?:'s|\s+is)\s+(?:the\s+)?weather|weather\s+today|weather\s+forecast|how\s+is\s+the\s+weather)\b", text, re.IGNORECASE):
            loc_match = re.search(r"\bweather\s+(?:in|for|at)\s+([a-zA-Z\s]+)", text, re.IGNORECASE)
            location = loc_match.group(1).strip() if loc_match else ""
            return Intent(category=IntentCategory.WEATHER, action="get_weather", params={"location": location})

        if re.search(r"(?:what(?:'s|\s+is)\s+the\s+time|tell\s+me\s+the\s+time|what\s+time\s+is\s+it|time\s+now|current\s+time)", text):
            return Intent(
                category=IntentCategory.TIME,
                action="get_time",
                params={},
            )

        if re.search(r"(?:what\s+(?:is\s+)?(?:today'?s\s+)?date|what\s+day\s+is\s+it|today'?s\s+date|what\s+is\s+the\s+date)", text):
            return Intent(
                category=IntentCategory.TIME,
                action="get_date",
                params={},
            )

        # ===================================================================
        # 4. WhatsApp & Communication Messaging
        # ===================================================================

        # Comprehensive messaging pattern:
        # "send a message to Lokesh"
        # "send a message to Jatin Mawa that I am coming today"
        # "send an imessage to Lokesh saying I will be late"
        # "send a whatsapp message to Lokesh that I am on my way"
        # "message Lokesh that I am coming"
        msg_match = re.search(
            r"^(?:send\s+(?:an?\s+)?(?:whatsapp\s+|whats\s*app\s+|imessage\s+|i\s*message\s+|text\s+)?message\s+to\s+|send\s+(?:an?\s+)?(?:whatsapp|whats\s*app|imessage|i\s*message|text)\s+to\s+|(?:message|text|whatsapp)\s+)(.+?)(?:\s+(?:that|saying\s+that|saying|telling\s+(?:him|her|them)\s+(?:that\s+)?|about|:)\s+(.+))?$",
            text,
            re.IGNORECASE,
        )
        if msg_match:
            contact = msg_match.group(1).strip()
            # Clean out any trailing "on whatsapp" if present in contact name
            contact = re.sub(r"\s+on\s+(?:whatsapp|whats\s*app|imessage)$", "", contact, flags=re.IGNORECASE).strip()
            message_body = msg_match.group(2).strip() if msg_match.group(2) else ""
            return Intent(
                category=IntentCategory.MESSAGING,
                target="WhatsApp",
                action="send_whatsapp",
                params={"contact": contact, "message": message_body},
            )

        # "message [name] on whatsapp" / "text [name] on whatsapp"
        wa_msg_match = re.search(r"(?:message|text)\s+(.+?)\s+on\s+(?:whatsapp|whats app)(?:\s+(?:that|saying|about)\s+(.+))?", text, re.IGNORECASE)
        if wa_msg_match:
            contact = wa_msg_match.group(1).strip()
            message_body = wa_msg_match.group(2).strip() if wa_msg_match.group(2) else ""
            return Intent(
                category=IntentCategory.MESSAGING,
                target="WhatsApp",
                action="send_whatsapp",
                params={"contact": contact, "message": message_body},
            )

        call_match = re.search(r"^(?:call|voice\s+call|video\s+call|ring)\s+(.+?)(?:\s+on\s+(?:whatsapp|whats\s*app|phone))?$", text, re.IGNORECASE)
        if call_match:
            contact = call_match.group(1).strip()
            return Intent(
                category=IntentCategory.MESSAGING,
                target="WhatsApp",
                action="call_contact",
                params={"contact": contact},
                requires_confirmation=True,
                confirmation_prompt=f"Calling {contact.title()} on WhatsApp.",
            )

        # "share this file to whatsapp"
        share_match = re.search(r"share\s+(?:this|the|my)\s+(?:file|document|image|video|photo)\s+(?:on|to|in)\s+(?:whatsapp|whats app)(?:\s+(?:for|to)\s+(.+))?", text, re.IGNORECASE)
        if share_match:
            contact = share_match.group(1) or ""
            return Intent(category=IntentCategory.MESSAGING, target="WhatsApp", action="share_file_whatsapp", params={"contact": contact.strip()})

        # "open whatsapp" (Desktop app)
        if re.search(r"\b(open|launch|start)\s+(?:whatsapp|whats app)\b", text, re.IGNORECASE):
            return Intent(category=IntentCategory.APP_LAUNCH, target="WhatsApp", action="launch_app", params={"app_name": "whatsapp"})

        # ===================================================================
        # 4.5. Folder Access & Browsing (In-Notch File View)
        # ===================================================================

        # User alias registration: "call my Client Files folder projects"
        alias_reg_match = re.search(r"\b(?:call|alias|name)\s+(?:my\s+)?(.+?)\s+folder\s+(.+)$", text, re.IGNORECASE)
        if alias_reg_match:
            folder_src = alias_reg_match.group(1).strip()
            alias_dst = alias_reg_match.group(2).strip()
            return Intent(
                category=IntentCategory.FOLDER_BROWSE,
                action="set_alias",
                params={"folder": folder_src, "alias": alias_dst},
            )

        # "what's in [folder] / what is in my [folder]"
        whats_in_match = re.search(r"\b(?:what'?s\s+(?:in|on)|what\s+is\s+(?:in|on)|show\s+me\s+what'?s\s+in)\s+(?:my\s+)?([a-zA-Z0-9\s]+?)(?:\s+folder)?$", text, re.IGNORECASE)
        if whats_in_match:
            target_f = whats_in_match.group(1).strip()
            if target_f in ["screen", "my screen", "the screen"]:
                pass  # goes to screen analysis
            else:
                return Intent(category=IntentCategory.FOLDER_BROWSE, action="browse_folder", params={"folder": target_f})

        # "open [folder] folder" / "show [folder] folder" / "browse [folder] folder"
        folder_named_match = re.search(r"\b(?:open|show|browse|view|display)\s+(?:my\s+)?([a-zA-Z0-9\s]+?)\s+folder\b", text, re.IGNORECASE)
        if folder_named_match:
            folder_target = folder_named_match.group(1).strip()
            return Intent(category=IntentCategory.FOLDER_BROWSE, action="browse_folder", params={"folder": folder_target})

        # Well-known folder direct shortcuts: "open downloads", "show screenshots", "open my desktop"
        well_known_match = re.search(r"\b(?:open|show|browse|view)\s+(?:my\s+)?(downloads?|screenshots?|desktop|documents?|pictures?|videos?|music)\b", text, re.IGNORECASE)
        if well_known_match:
            folder_target = well_known_match.group(1).strip()
            return Intent(category=IntentCategory.FOLDER_BROWSE, action="browse_folder", params={"folder": folder_target})

        # ===================================================================
        # 4.7. Prompt Generation & Engineering
        # ===================================================================

        # "give me a prompt for tagged box" / "generate a prompt for health app" / "prompt for tagged box"
        prompt_match = re.search(
            r"^(?:(?:can\s+you\s+|please\s+)?(?:give\s+(?:me\s+)?(?:a\s+)?|generate\s+(?:a\s+)?|create\s+(?:a\s+)?|write\s+(?:a\s+)?|make\s+(?:a\s+)?|build\s+(?:a\s+)?)(?:polished\s+|good\s+|system\s+)?prompt\s+(?:for|about|to|on)\s+|prompt\s+(?:for|about|on)\s+)(.+)$",
            text,
            re.IGNORECASE,
        )
        if prompt_match:
            topic = prompt_match.group(1).strip()
            topic = re.sub(r"[?.!]+$", "", topic).strip()
            return Intent(
                category=IntentCategory.PROMPT_GEN,
                target="PromptGenerator",
                action="generate_prompt",
                params={"topic": topic},
            )

        # ===================================================================
        # 5. Email
        # ===================================================================

        # Read / Check Gmails or Inbox
        # "read my gmails", "check my emails", "read emails", "read gmail", "check my inbox", "show my emails"
        if re.search(r"\b(?:read|check|show|fetch|get)\s+(?:my\s+)?(?:unread\s+)?(?:gmails?|emails?|mails?|inbox)\b", text, re.IGNORECASE):
            return Intent(
                category=IntentCategory.EMAIL,
                target="Gmail",
                action="read_emails",
                params={},
            )

        # "send an email to [person] about [subject]" / "email [person] saying [body]"
        email_match = re.search(
            r"(?:send\s+(?:an?\s+)?(?:email|mail)\s+to\s+)(.+?)(?:\s+(?:about|regarding|subject|saying)\s+(.+))?$", text
        )
        if email_match:
            recipient = email_match.group(1).strip()
            subject = email_match.group(2).strip() if email_match.group(2) else ""
            return Intent(
                category=IntentCategory.EMAIL,
                target="Gmail",
                action="compose_email",
                params={"recipient": recipient, "subject": subject},
            )

        # "compose email" / "new email" / "write an email" / "send an email"
        if re.search(r"\b(send|compose|write|draft|new)\s+(?:an?\s+)?(?:email|mail)\b", text):
            return Intent(
                category=IntentCategory.EMAIL,
                target="Gmail",
                action="compose_email",
                params={"recipient": "", "subject": ""},
            )

        # "open email" / "open gmail" (Explicit webmail navigation)
        if re.search(r"\b(?:open|launch)\s+(?:my\s+)?(?:email|emails|mail|inbox|gmail)\b", text, re.IGNORECASE):
            return Intent(
                category=IntentCategory.WEB_NAVIGATION,
                target="Gmail",
                action="open_url",
                params={"url": "https://mail.google.com"},
            )

        # ===================================================================
        # 6. Telegram
        # ===================================================================

        tg_send_match = re.search(r"(?:send\s+(?:a\s+)?telegram\s+(?:message\s+)?to\s+)(.+?)(?:\s+saying\s+(.+))?$", text)
        if tg_send_match:
            contact = tg_send_match.group(1).strip()
            message_body = tg_send_match.group(2).strip() if tg_send_match.group(2) else ""
            return Intent(
                category=IntentCategory.MESSAGING,
                target="Telegram",
                action="send_telegram",
                params={"contact": contact, "message": message_body},
            )

        if re.search(r"\b(open|launch|start)\s+telegram\b", text):
            return Intent(category=IntentCategory.APP_LAUNCH, target="Telegram", action="launch_app", params={"app_name": "telegram"})

        # ===================================================================
        # 7. SMS / General Messaging
        # ===================================================================

        sms_match = re.search(r"(?:send\s+(?:a\s+)?(?:message|text|sms)\s+to\s+)(.+?)(?:\s+saying\s+(.+))?$", text)
        if sms_match and "whatsapp" not in text and "telegram" not in text and "email" not in text:
            contact = sms_match.group(1).strip()
            message_body = sms_match.group(2).strip() if sms_match.group(2) else ""
            return Intent(
                category=IntentCategory.MESSAGING,
                target="WhatsApp",
                action="send_whatsapp",
                params={"contact": contact, "message": message_body},
            )

        # ===================================================================
        # 8. Phone Call (via WhatsApp or link)
        # Strict pattern: MUST explicitly begin with an actual call command (e.g. "call Rahul")
        # Never match devices like "iphone", "headphone", "earphone", or search phrases.
        # ===================================================================

        call_match = re.search(r"^(?:make\s+(?:a\s+)?(?:phone\s+)?call\s+to|call|phone|ring)\s+([a-zA-Z\s]+?)(?:\s+on\s+(?:whatsapp|whats app))?$", text, re.IGNORECASE)
        if call_match:
            contact = call_match.group(1).strip()
            contact_lower = contact.lower()
            non_contacts = {
                "iphone", "phone", "headphone", "headphones", "earphone", "earphones",
                "microphone", "smartphone", "smartphones", "cellphone", "android", "mobile",
                "it", "me", "this", "that", "them", "him", "her", "someone", "anyone", "number",
                "18 pro", "17 pro", "16 pro", "15 pro", "14 pro", "police", "help", "jarvis", "google"
            }
            if contact_lower not in non_contacts and not any(dev in contact_lower for dev in ["iphone", "pixel", "galaxy", "headphone", "earphone"]):
                return Intent(
                    category=IntentCategory.PHONE_CALL,
                    target="WhatsApp",
                    action="call_contact",
                    params={"contact": contact.title()},
                )

        # ===================================================================
        # 9. System Lock & Power
        # ===================================================================

        if re.search(r"\b(lock\s+(my\s+)?(pc|computer|screen|workstation|laptop))|(lock it)\b", text):
            return Intent(category=IntentCategory.SYSTEM_CONTROL, action="lock_pc")

        if re.search(r"\b(shut\s*down|power\s+off|turn\s+off)\s+(my\s+)?(pc|computer|laptop)\b", text):
            return Intent(
                category=IntentCategory.SYSTEM_CONTROL,
                action="shutdown",
                requires_confirmation=True,
                confirmation_prompt="Are you sure you want to shut down the computer?",
            )

        if re.search(r"\b(restart|reboot)\s+(my\s+)?(pc|computer|laptop)\b", text):
            return Intent(
                category=IntentCategory.SYSTEM_CONTROL,
                action="restart_pc",
                requires_confirmation=True,
                confirmation_prompt="Are you sure you want to restart the computer?",
            )

        if re.search(r"\b(sleep|hibernate)\s+(my\s+)?(pc|computer|laptop)\b", text) or text == "go to sleep":
            return Intent(category=IntentCategory.SYSTEM_CONTROL, action="sleep_pc")

        # ===================================================================
        # 10. Volume Controls
        # ===================================================================

        if "volume up" in text or "increase volume" in text or "louder" in text or "turn up volume" in text:
            return Intent(category=IntentCategory.SYSTEM_CONTROL, action="volume_up")
        if "volume down" in text or "decrease volume" in text or "quieter" in text or "turn down volume" in text or "lower volume" in text:
            return Intent(category=IntentCategory.SYSTEM_CONTROL, action="volume_down")
        if text in ["mute", "unmute", "toggle mute"] or "mute" in text:
            return Intent(category=IntentCategory.SYSTEM_CONTROL, action="mute")

        # Set volume to X%
        vol_match = re.search(r"(?:set\s+)?volume\s+(?:to\s+)?(\d+)\s*%?", text)
        if vol_match:
            level = int(vol_match.group(1))
            return Intent(category=IntentCategory.SYSTEM_CONTROL, action="set_volume", params={"level": level})

        # ===================================================================
        # 11. Brightness Controls
        # ===================================================================

        if "brightness up" in text or "increase brightness" in text or "brighter" in text:
            return Intent(category=IntentCategory.SYSTEM_CONTROL, action="brightness_up")
        if "brightness down" in text or "decrease brightness" in text or "dimmer" in text or "dim screen" in text:
            return Intent(category=IntentCategory.SYSTEM_CONTROL, action="brightness_down")

        # ===================================================================
        # 12. Media Controls (Play/Pause/Skip)
        # ===================================================================

        if text in ["play", "resume", "play music", "resume music", "unpause"]:
            return Intent(category=IntentCategory.MEDIA_CONTROL, action="play_pause")
        if text in ["pause", "pause music", "pause video"]:
            return Intent(category=IntentCategory.MEDIA_CONTROL, action="play_pause")
        if text in ["next", "next song", "next track", "skip", "skip song"]:
            return Intent(category=IntentCategory.MEDIA_CONTROL, action="next_track")
        if text in ["previous", "previous song", "previous track", "go back", "last song"]:
            return Intent(category=IntentCategory.MEDIA_CONTROL, action="previous_track")

        # "open [app] and play [song/movie]"
        open_and_play = re.search(r"^(?:open|launch)\s+([a-zA-Z0-9\s]+?)\s+and\s+play\s+(.+)$", text)
        if open_and_play:
            platform = open_and_play.group(1).strip()
            query = open_and_play.group(2).strip()
            return Intent(category=IntentCategory.WEB_NAVIGATION, target="Browser", action="lucky_search", params={"query": f"watch {query} on {platform}"})

        # "play [song] on youtube/spotify" or "play [song]"
        play_match = re.search(r"^play\s+(.+?)(?:\s+on\s+([a-zA-Z0-9\s]+))?$", text)
        if play_match and text.startswith("play "):
            query = play_match.group(1).strip()
            platform = (play_match.group(2) or "").lower()

            # If user explicitly specifies spotify or youtube
            if platform == "spotify" or "spotify" in query.lower():
                clean_q = re.sub(r"\b(on\s+spotify|in\s+spotify|spotify)\b", "", query, flags=re.IGNORECASE).strip()
                return Intent(category=IntentCategory.MUSIC, target="Spotify", action="play_spotify", params={"query": clean_q or query})
            elif platform == "youtube" or "youtube" in query.lower():
                clean_q = re.sub(r"\b(on\s+youtube|in\s+youtube|youtube)\b", "", query, flags=re.IGNORECASE).strip()
                return Intent(category=IntentCategory.MUSIC, target="YouTube", action="play_youtube", params={"query": clean_q or query})
            elif platform:
                return Intent(category=IntentCategory.WEB_NAVIGATION, target="Browser", action="lucky_search", params={"query": f"watch {query} on {platform}"})
            else:
                # Default music query to YouTube playback for direct audio/video streaming
                return Intent(category=IntentCategory.MUSIC, target="YouTube", action="play_youtube", params={"query": query})

        # ===================================================================
        # 13. Window Controls (Minimize, Maximize, Close active)
        # ===================================================================

        if text in ["close window", "close this window", "close this", "close active window"]:
            return Intent(category=IntentCategory.WINDOW_CONTROL, action="close_active")

        if re.search(r"\b(minimize(\s+this)?(\s+window)?)\b", text):
            return Intent(category=IntentCategory.WINDOW_CONTROL, action="minimize")
        if re.search(r"\b(maximize(\s+this)?(\s+window)?)\b", text):
            return Intent(category=IntentCategory.WINDOW_CONTROL, action="maximize")

        # Split screen / snap
        if "snap left" in text or "move left" in text:
            return Intent(category=IntentCategory.KEYBOARD_SHORTCUT, action="hotkey", params={"keys": ["win", "left"]})
        if "snap right" in text or "move right" in text:
            return Intent(category=IntentCategory.KEYBOARD_SHORTCUT, action="hotkey", params={"keys": ["win", "right"]})

        # ===================================================================
        # 14. Screenshot
        # ===================================================================

        if text in ["take a screenshot", "screenshot", "capture screen", "take screenshot", "screen capture", "snip"]:
            return Intent(category=IntentCategory.SCREENSHOT, action="screenshot")

        # ===================================================================
        # 15. Clipboard
        # ===================================================================

        if text in ["copy", "copy that", "copy this"]:
            return Intent(category=IntentCategory.KEYBOARD_SHORTCUT, action="hotkey", params={"keys": ["ctrl", "c"]})
        if text in ["paste", "paste that", "paste it"]:
            return Intent(category=IntentCategory.KEYBOARD_SHORTCUT, action="hotkey", params={"keys": ["ctrl", "v"]})
        if text in ["cut", "cut this", "cut that"]:
            return Intent(category=IntentCategory.KEYBOARD_SHORTCUT, action="hotkey", params={"keys": ["ctrl", "x"]})
        if text in ["undo", "undo that"]:
            return Intent(category=IntentCategory.KEYBOARD_SHORTCUT, action="hotkey", params={"keys": ["ctrl", "z"]})
        if text in ["redo", "redo that"]:
            return Intent(category=IntentCategory.KEYBOARD_SHORTCUT, action="hotkey", params={"keys": ["ctrl", "y"]})
        if text in ["select all", "select everything"]:
            return Intent(category=IntentCategory.KEYBOARD_SHORTCUT, action="hotkey", params={"keys": ["ctrl", "a"]})

        # ===================================================================
        # 16. Popular Website Direct Launching
        # ===================================================================

        # Clean text for website checks
        clean_web_text = re.sub(r"^(?:please\s+|can\s+you\s+)?(?:open|launch|go\s+to|take\s+me\s+to)\s+(?:the\s+)?", "", text).strip()
        clean_web_text = re.sub(r"\s+please$", "", clean_web_text).strip()

        for site_name, site_url in POPULAR_SITES.items():
            if clean_web_text == site_name or text == f"open {site_name}" or text == f"go to {site_name}" or text == f"launch {site_name}":
                if site_name == "youtube":
                    return Intent(category=IntentCategory.WEB_NAVIGATION, target="YouTube", action="open_youtube")
                return Intent(category=IntentCategory.WEB_NAVIGATION, target=site_name.replace(" ", "").title(), action="open_url", params={"url": site_url})

        # ===================================================================
        # 17. YouTube & Web Searches
        # ===================================================================

        yt_search_match = re.search(r"search\s+(youtube\s+for|for)\s+(.+?)(\s+on\s+youtube)?$", text)
        if ("youtube" in text and "search" in text) or (context_engine.get_active_target() == "YouTube" and text.startswith("search")):
            query = ""
            if "for" in text:
                query = text.split("for", 1)[1].replace("on youtube", "").replace("youtube", "").strip()
            elif "search" in text:
                query = text.replace("search", "").replace("youtube", "").strip()
            if query:
                return Intent(category=IntentCategory.WEB_SEARCH, target="YouTube", action="search_youtube", params={"query": query})

        # Open YouTube
        if re.search(r"\b(open|launch|go to|take me to)\s+youtube\b", text):
            return Intent(category=IntentCategory.WEB_NAVIGATION, target="YouTube", action="open_youtube")

        # Generic Web Search: "search google for..." or "google..." or "search for..."
        if text.startswith("search google for ") or text.startswith("google "):
            q = text.replace("search google for ", "").replace("google ", "").strip()
            return Intent(category=IntentCategory.WEB_SEARCH, target="Google", action="search_google", params={"query": q})

        if text.startswith("search for ") and "file" not in text:
            q = text.replace("search for ", "").strip()
            return Intent(category=IntentCategory.WEB_SEARCH, target="Google", action="search_google", params={"query": q})

        # "search [query]"
        if text.startswith("search ") and "file" not in text and "youtube" not in text:
            q = text.replace("search ", "").strip()
            if q:
                return Intent(category=IntentCategory.WEB_SEARCH, target="Google", action="search_google", params={"query": q})

        # Open Web URL: e.g. "open github.com"
        url_match = re.search(r"\b(open|go to)\s+([a-zA-Z0-9-]+\.(com|org|net|io|dev|ai|edu|gov|in|co))\b", text)
        if url_match:
            return Intent(category=IntentCategory.WEB_NAVIGATION, target="Browser", action="open_url", params={"url": url_match.group(2)})

        # Open generic website: "open movie rules", "open net mirror"
        generic_open_match = re.search(r"^(?:please\s+|can\s+you\s+)?(?:open|launch|go\s+to|start)\s+([a-zA-Z0-9\s]+?)(?:\s+website|site)?$", text)
        if generic_open_match:
            site_query = generic_open_match.group(1).strip()
            if site_query not in ["the", "my", "a"]:
                common_apps = ["notepad", "calculator", "calc", "cmd", "terminal", "powershell", "settings", "word", "excel", "powerpoint", "vscode", "code", "paint", "chrome", "edge", "spotify"]
                if site_query.lower() in common_apps:
                    return Intent(category=IntentCategory.APP_LAUNCH, target=site_query.title(), action="launch_app", params={"app_name": site_query.lower()})
                # Exclude local folders handled earlier, though they are usually caught by earlier regexes
                if site_query not in ["downloads", "screenshots", "desktop", "documents", "pictures", "videos", "music", "settings", "file explorer", "whatsapp", "this pc"]:
                    return Intent(category=IntentCategory.WEB_NAVIGATION, target="Browser", action="lucky_search", params={"query": site_query})

        # Scrolling
        if "scroll down" in text:
            return Intent(category=IntentCategory.BROWSER_ACTION, action="scroll_down")
        if "scroll up" in text:
            return Intent(category=IntentCategory.BROWSER_ACTION, action="scroll_up")

        # Browser Tabs
        if "new tab" in text or "open tab" in text:
            return Intent(category=IntentCategory.BROWSER_ACTION, action="new_tab")
        if "close tab" in text:
            return Intent(category=IntentCategory.BROWSER_ACTION, action="close_tab")
        if "refresh" in text or "reload" in text:
            return Intent(category=IntentCategory.BROWSER_ACTION, action="refresh")
        if "go back" in text or "back page" in text:
            return Intent(category=IntentCategory.BROWSER_ACTION, action="back")
        if "go forward" in text or "forward page" in text:
            return Intent(category=IntentCategory.BROWSER_ACTION, action="forward")

        # ===================================================================
        # 18. Windows Applications Launch / Close / Focus
        # ===================================================================

        # Specific app shortcuts that would be caught by generic patterns
        if text in ["open file explorer", "launch file explorer", "file explorer"]:
            return Intent(category=IntentCategory.KEYBOARD_SHORTCUT, action="hotkey", params={"keys": ["win", "e"]})
        if text in ["open task manager", "task manager", "launch task manager"]:
            return Intent(category=IntentCategory.KEYBOARD_SHORTCUT, action="hotkey", params={"keys": ["ctrl", "shift", "escape"]})

        # ===================================================================
        # 18. File & Folder Opening
        # Matches:
        # - "open the video file", "open video file", "open videos", "open video folder"
        # - "open the screenshot file", "open screenshot file", "open screenshots", "open screenshot folder"
        # - "open the movies file", "open movie file", "open movies", "open movies folder"
        # - "open the downloads file", "open download file", "open downloads"
        # - "open the documents file", "open documents"
        # - "open the pictures file", "open pictures", "open photos"
        # - "open the music file", "open music", "open songs"
        # - "open the desktop file", "open desktop"
        # ===================================================================

        file_folder_match = re.search(
            r"^(?:open|show|launch|view)\s+(?:the\s+|my\s+)?(video|videos|screenshot|screenshots|movie|movies|film|films|download|downloads|document|documents|picture|pictures|photo|photos|image|images|music|song|songs|desktop)(?:\s+file|\s+files|\s+folder|\s+directory)?$",
            text,
            re.IGNORECASE
        )
        if file_folder_match:
            folder_target = file_folder_match.group(1).lower()
            if "file" in text or "image" in text or "photo" in text or "song" in text:
                return Intent(category=IntentCategory.FILE_OPEN, target="Filesystem", action="open_latest_file", params={"folder": folder_target})
            return Intent(category=IntentCategory.FILE_OPEN, target="Filesystem", action="open_folder", params={"folder": folder_target})

        # Any explicit folder or directory command: "open project folder", "open client files directory"
        generic_folder_match = re.search(r"^(?:open|show|launch|view)\s+(?:the\s+|my\s+)?(.+?)\s+(?:folder|directory)$", text, re.IGNORECASE)
        if generic_folder_match:
            f_name = generic_folder_match.group(1).strip()
            return Intent(category=IntentCategory.FILE_OPEN, target="Filesystem", action="open_folder", params={"folder": f_name})

        # "open [name] file" / "open the [name] file" (e.g. "open resume file", "open notes file")
        specific_file_match = re.search(
            r"^(?:open|show|launch|view)\s+(?:the\s+|my\s+)?([a-zA-Z0-9_\-\.\s]+?)\s+(?:file|document|pdf|script|sheet)$",
            text,
            re.IGNORECASE
        )
        if specific_file_match:
            q = specific_file_match.group(1).strip()
            if q and q not in ["a", "the", "my"]:
                return Intent(category=IntentCategory.FILE_OPEN, target="Filesystem", action="open_file", params={"query": q})

        # File with extension: "open resume.pdf", "open test.py", "open data.xlsx"
        ext_file_match = re.search(
            r"^(?:open|launch)\s+(?:the\s+|my\s+)?([a-zA-Z0-9_\-]+\.(?:pdf|txt|docx|doc|xlsx|csv|py|js|ts|json|png|jpg|jpeg|mp4|mkv|avi|zip))$",
            text,
            re.IGNORECASE
        )
        if ext_file_match:
            q = ext_file_match.group(1).strip()
            return Intent(category=IntentCategory.FILE_OPEN, target="Filesystem", action="open_file", params={"query": q})

        launch_match = re.search(r"^(open|launch|start|run)\s+([a-zA-Z0-9\s]+)$", text)
        if launch_match:
            app_raw = launch_match.group(2).strip()
            # Skip calendar, portfolio, and linkedin commands here
            if "calendar" in app_raw or "linkedin" in app_raw or "portfolio" in app_raw:
                pass
            elif app_raw not in POPULAR_SITES:
                # Check if it's an explicit file request
                if "file" in app_raw or app_raw.endswith((".pdf", ".txt", ".docx", ".png")):
                    query = app_raw.replace("my ", "").replace("the ", "").replace("file", "").strip()
                    return Intent(category=IntentCategory.FILE_OPEN, target="Filesystem", action="open_file", params={"query": query})

                return Intent(category=IntentCategory.APP_LAUNCH, target=app_raw.title(), action="launch_app", params={"app_name": app_raw})

        close_match = re.search(r"^(close|quit|exit|kill)\s+([a-zA-Z0-9\s]+)$", text)
        if close_match:
            app_raw = close_match.group(2).strip()
            return Intent(category=IntentCategory.APP_CLOSE, target=app_raw.title(), action="close_app", params={"app_name": app_raw})

        focus_match = re.search(r"^(switch to|focus|bring up|go to|alt tab to)\s+([a-zA-Z0-9\s]+)$", text)
        if focus_match:
            app_raw = focus_match.group(2).strip()
            if app_raw not in POPULAR_SITES:
                return Intent(category=IntentCategory.APP_FOCUS, target=app_raw.title(), action="focus_app", params={"app_name": app_raw})

        # ===================================================================
        # 19. Screen & Cursor Vision (Point Anywhere on Screen)
        # ===================================================================

        # Point and ask: "find his LinkedIn", "open his LinkedIn", "find this person's LinkedIn", "find linkedin"
        if re.search(r"\b(?:find|open|show|get|search|look\s+up|pull\s+up|check)\s+(?:his|her|their|this\s+person'?s?|the|a)?\s*linkedin\b", text) or \
           re.search(r"\b(?:find|search|look\s+up)\s+linkedin\b", text) or \
           re.search(r"\bcan\s+you\s+find\s+(?:the\s+linkedin\s+of|his|her|their\s+linkedin|linkedin)\b", text) or \
           re.search(r"\blinkedin\s+profile\b", text):
            return Intent(
                category=IntentCategory.CURSOR_ANALYSIS,
                action="find_linkedin",
                params={"prompt": "Extract the person's full name and company/title from the text visible near the cursor. Respond strictly with 'Name - Company/Title'. If no name is clearly identifiable in the text, respond strictly with 'NO_NAME_FOUND'."},
            )

        # Point and ask: "what is this", "who is this", "explain this", "read this", "read what's on my screen", "what am I pointing at"
        if re.search(r"\b(?:what\s+is\s+this|what'?s\s+this|who\s+is\s+this|who'?s\s+this|what\s+does\s+this\s+(?:mean|do)|explain\s+this|describe\s+this|summarize\s+this|read\s+this|read\s+(?:what'?s\s+on\s+my\s+screen|my\s+screen|this\s+screen|the\s+screen)|what\s+am\s+i\s+(?:looking|pointing)\s+at|read\s+what\s+i'?m\s+pointing\s+at|what'?s\s+under\s+(?:my\s+)?cursor)\b", text):
            return Intent(category=IntentCategory.CURSOR_ANALYSIS, action="analyze", params={"prompt": "Identify the subject or text at the cursor (text, code, diagram, button, person, object) and give a concise, useful explanation or read what is written."})

        # Deep Explanation (Knowledge/Interview Prep)
        deep_match = re.search(r"^(?:explain\s+(?:to\s+me\s+)?|what\s+is\s+|tell\s+me\s+about\s+|prepare\s+me\s+for\s+|prep\s+me\s+for\s+|what\s+do\s+you\s+know\s+about\s+)(.+)$", text, re.IGNORECASE)
        # We need to make sure it doesn't conflict with screen commands
        if deep_match and "screen" not in text and "this" not in text.split() and "page" not in text:
            topic = deep_match.group(1).strip()
            return Intent(category=IntentCategory.DEEP_EXPLANATION, target="AIQuery", action="deep_explanation", params={"topic": topic})

        # ===================================================================
        # 19.5. Autonomous Job Application Agent ("Apply for this")
        # ===================================================================
        if re.search(r"\b(?:apply\s+(?:for\s+)?(?:this\s+)?(?:job|role|position)|apply\s+for\s+this|apply\s+to\s+this|apply\s+here|auto\s*apply|fill\s+(?:this\s+)?(?:application|form)|apply\s+now)\b", text):
            return Intent(category=IntentCategory.JOB_APPLICATION, target="JobApplicant", action="apply_for_job", params={})

        if re.search(r"\b(?:show|view|get|check|display)\s+(?:my\s+)?(?:resume|profile|details|projects)\b|\b(?:what\s+is\s+on\s+my\s+resume|my\s+resume)\b", text):
            return Intent(category=IntentCategory.JOB_APPLICATION, target="JobApplicant", action="get_profile", params={})

        # Full screen analysis: "what's on my screen", "explain this page"
        if re.search(r"\b(?:what\s+is\s+on\s+my\s+screen|what'?s\s+on\s+my\s+screen|explain\s+this\s+page|read\s+this\s+error|analyze\s+screen|read\s+screen|explain\s+screen)\b", text):
            return Intent(category=IntentCategory.SCREEN_ANALYSIS, action="analyze", params={"prompt": text})

        # ===================================================================
        # 20. File System
        # ===================================================================

        find_match = re.search(r"^(find|search for|locate)\s+(my\s+)?([a-zA-Z0-9\s\.\-_]+)$", text)
        if find_match and "youtube" not in text and "google" not in text and "linkedin" not in text:
            query = find_match.group(3).replace("file", "").strip()
            return Intent(category=IntentCategory.FILE_SEARCH, target="Filesystem", action="find_file", params={"query": query})

        # Create folder
        folder_match = re.search(r"create\s+(a\s+)?folder\s+(called|named)?\s*([a-zA-Z0-9_-]+)", text)
        if folder_match:
            name = folder_match.group(3).strip()
            return Intent(category=IntentCategory.FILE_CREATE, target="Filesystem", action="create_folder", params={"name": name})

        # Create file
        file_create_match = re.search(r"create\s+(a\s+)?file\s+(called|named)?\s*([a-zA-Z0-9_\-\.]+)", text)
        if file_create_match:
            name = file_create_match.group(3).strip()
            return Intent(category=IntentCategory.FILE_CREATE, target="Filesystem", action="create_file", params={"name": name})

        # Delete: "delete the file test.txt" -> Consequential!
        del_match = re.search(r"delete\s+(the\s+file\s+)?([a-zA-Z0-9_\-\.]+)", text)
        if del_match:
            target_name = del_match.group(2).strip()
            return Intent(
                category=IntentCategory.FILE_DELETE,
                target="Filesystem",
                action="delete_file",
                params={"target": target_name},
                requires_confirmation=True,
                confirmation_prompt=f"Delete file: {target_name}",
            )

        # ===================================================================
        # 20. Keyboard Shortcuts
        # ===================================================================

        if text in ["task manager", "open task manager"]:
            return Intent(category=IntentCategory.KEYBOARD_SHORTCUT, action="hotkey", params={"keys": ["ctrl", "shift", "escape"]})
        if text in ["show desktop", "desktop", "go to desktop"]:
            return Intent(category=IntentCategory.KEYBOARD_SHORTCUT, action="hotkey", params={"keys": ["win", "d"]})
        if text in ["task view", "virtual desktops", "show all windows"]:
            return Intent(category=IntentCategory.KEYBOARD_SHORTCUT, action="hotkey", params={"keys": ["win", "tab"]})
        if text in ["action center", "notifications", "notification center"]:
            return Intent(category=IntentCategory.KEYBOARD_SHORTCUT, action="hotkey", params={"keys": ["win", "a"]})
        if text in ["file explorer", "open file explorer", "my computer", "this pc"]:
            return Intent(category=IntentCategory.KEYBOARD_SHORTCUT, action="hotkey", params={"keys": ["win", "e"]})
        if text in ["settings", "open settings", "system settings", "windows settings"]:
            return Intent(category=IntentCategory.APP_LAUNCH, target="Settings", action="launch_app", params={"app_name": "settings"})
        if text in ["emoji", "emojis", "open emoji", "emoji picker"]:
            return Intent(category=IntentCategory.KEYBOARD_SHORTCUT, action="hotkey", params={"keys": ["win", "."]})

        # ===================================================================
        # 21. Screen & Cursor Vision
        # ===================================================================

        if text in ["what is on my screen", "explain this page", "read this error", "what is on my screen?", "analyze screen", "read screen", "what's on my screen"]:
            return Intent(category=IntentCategory.SCREEN_ANALYSIS, action="analyze", params={"prompt": text})

        if re.search(r"(?:what\s+is\s+this|what'?s\s+this|what\s+does\s+this\s+do|explain\s+this|describe\s+this|what\s+am\s+i\s+(?:looking|pointing)\s+at)", text):
            return Intent(category=IntentCategory.CURSOR_ANALYSIS, action="analyze", params={"prompt": text})

        # ===================================================================
        # 22. VoiceOS Dictation: "dictate: ..." or "type ..."
        # ===================================================================

        if text.startswith("dictate ") or text.startswith("type "):
            clean_dictation = text.replace("dictate ", "", 1).replace("type ", "", 1)
            return Intent(category=IntentCategory.DICTATION, action="dictate", params={"text": clean_dictation})

        # ===================================================================
        # 23. Reminders (spoken acknowledgment)
        # ===================================================================

        # ===================================================================
        # 23. Calendar & Scheduled Reminders
        # ===================================================================

        if "calendar" in text:
            if text in ["open calendar", "show my calendar", "calendar", "launch calendar", "open my calendar", "open google calendar"]:
                return Intent(category=IntentCategory.CALENDAR, action="open_calendar")

            from jarvis.tools.calendar_tool import CalendarTool
            cal_tool = CalendarTool()
            clean_title, extracted_date, extracted_time = cal_tool._clean_event_title(text)

            time_str = extracted_time or "9:00 AM"
            if extracted_date:
                date_str = extracted_date.strftime("%Y-%m-%d")
                date_prompt = extracted_date.strftime("%A, %B %d")
            else:
                date_str = "today"
                date_prompt = "today"

            return Intent(
                category=IntentCategory.CALENDAR,
                action="create_event",
                params={
                    "title": clean_title,
                    "time": time_str,
                    "date": date_str,
                },
                confirmation_prompt=f"I've opened your calendar and scheduled '{clean_title}' for {date_prompt} at {time_str}."
            )

        cal_meeting_match = re.search(r"schedule\s+a\s+meeting\s+with\s+(.+?)\s+on\s+(.+?)(?:\s+at\s+(.+))?$", text)
        if cal_meeting_match:
            return Intent(
                category=IntentCategory.CALENDAR,
                action="create_event",
                params={
                    "title": f"Meeting with {cal_meeting_match.group(1)}",
                    "date": cal_meeting_match.group(2).strip(),
                    "time": cal_meeting_match.group(3).strip() if cal_meeting_match.group(3) else "",
                }
            )

        # Standalone reminders with clock time
        remind_clock_match = re.search(r"remind\s+me\s+(?:at\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\s+)?(?:to\s+|that\s+|i\s+need\s+to\s+)?(.+)", text)
        if remind_clock_match and remind_clock_match.group(1):
            event_time = remind_clock_match.group(1)
            task_title = remind_clock_match.group(2).strip().capitalize()
            return Intent(
                category=IntentCategory.CALENDAR,
                action="create_event",
                params={
                    "title": task_title,
                    "time": event_time,
                    "date": "today",
                    "full_details": f"Reminder: {task_title}\nTime: {event_time}\nStatus: Scheduled in Calendar"
                },
                confirmation_prompt=f"I've scheduled a reminder to {task_title} at {event_time}."
            )

        # Relative timer reminders: "remind me to call mom in 10 minutes"
        remind_match = re.search(r"remind\s+me\s+(?:to\s+)?(.+?)\s+in\s+(\d+)\s+(minutes?|hours?|seconds?)$", text)
        if remind_match:
            task = remind_match.group(1).strip()
            amount = int(remind_match.group(2))
            unit = remind_match.group(3)
            return Intent(
                category=IntentCategory.REMINDER,
                action="set_reminder",
                params={"task": task, "amount": amount, "unit": unit},
                confirmation_prompt=f"I'll remind you to {task} in {amount} {unit}."
            )

        # ===================================================================
        # 26. Tasks & Todos
        # ===================================================================

        if text in ["what are my tasks", "list my tasks", "show my tasks", "what do i need to do", "my tasks", "my todos"]:
            return Intent(category=IntentCategory.TASK, action="list_tasks", params={"status": "pending"})

        task_add_match = re.search(r"(?:add\s+to\s+(?:my\s+)?(?:todo\s+list|tasks?)|remind\s+me\s+to|todo)\s+(.+?)(?:\s+due\s+(.+))?$", text)
        if task_add_match:
            return Intent(
                category=IntentCategory.TASK,
                action="add_task",
                params={
                    "title": task_add_match.group(1).strip(),
                    "due": task_add_match.group(2).strip() if task_add_match.group(2) else ""
                }
            )

        task_done_match = re.search(r"(?:mark|set)\s+(?:task|todo)\s+(.+?)\s+as\s+(?:done|complete|completed)", text)
        if task_done_match:
            return Intent(category=IntentCategory.TASK, action="complete_task", params={"query": task_done_match.group(1).strip()})

        # ===================================================================
        # 27. Memory
        # ===================================================================

        if text in ["what do you remember", "list memories"]:
            return Intent(category=IntentCategory.MEMORY, action="list_memories")

        mem_store_match = re.search(r"(?:remember|memorize)\s+that\s+(.+?)\s+(?:is|are)\s+(.+)", text)
        if mem_store_match:
            return Intent(category=IntentCategory.MEMORY, action="remember", params={"key": mem_store_match.group(1).strip(), "value": mem_store_match.group(2).strip()})

        # Personal memory recall must strictly require 'my' or 'remember about'
        mem_recall_match = re.search(r"(?:what\s+(?:is|are)|who\s+is)\s+my\s+(.+?)$|^(?:recall|what do you remember about)\s+(.+?)$", text)
        if mem_recall_match:
            query_term = (mem_recall_match.group(1) or mem_recall_match.group(2) or "").strip()
            if query_term:
                return Intent(category=IntentCategory.MEMORY, action="recall", params={"query": query_term})

        history_match = re.search(r"what did i ask (you\s+)?(yesterday|today|last week|recently)", text)
        if history_match:
            return Intent(category=IntentCategory.MEMORY, action="recall_history", params={"timeframe": history_match.group(2).strip()})

        # ===================================================================
        # 28. Calendar & Reminders
        # ===================================================================

        # "open calendar and set a reminder for X at Y" - extract title properly
        cal_reminder = re.search(
            r"(?:set\s+(?:a\s+)?(?:reminder|event|meeting)|schedule|add\s+(?:a\s+)?(?:event|reminder|meeting))"
            r"\s+(?:for\s+)?(.+?)(?:\s+(?:at|on|for)\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm|a\.m\.|p\.m\.)?))?$",
            text,
        )
        if cal_reminder:
            title = cal_reminder.group(1).strip().rstrip(" at on for")
            time_str = cal_reminder.group(2) or ""
            return Intent(
                category=IntentCategory.CALENDAR,
                action="create_event",
                params={"title": title.capitalize(), "time": time_str, "date": "today"},
            )

        # "open calendar" / "open my calendar"
        if re.search(r"\b(?:open|show|launch)\s+(?:my\s+)?(?:calendar|google calendar)\b", text):
            return Intent(category=IntentCategory.CALENDAR, action="open_calendar", params={})

        # ===================================================================
        # 29. Cursor / Screen Analysis (Point-and-Ask)
        # ===================================================================

        # "what is this" / "what am I looking at" / "what's this" / "explain this"
        if re.search(r"(?:what\s+is\s+this|what'?s\s+this|what\s+am\s+i\s+(?:looking|pointing)\s+at|explain\s+this|describe\s+this|what\s+do\s+you\s+see)", text):
            return Intent(
                category=IntentCategory.CURSOR_ANALYSIS,
                action="analyze",
                params={"prompt": "Describe what the user is pointing at on their screen. What is this element?"},
            )

        # "what is on my screen" / "analyze my screen" / "read my screen"
        if re.search(r"(?:what\s+is\s+on\s+(?:my\s+)?screen|analyze\s+(?:my\s+)?screen|read\s+(?:my\s+)?screen|what\s+do\s+you\s+see\s+on\s+(?:my\s+)?screen)", text):
            return Intent(
                category=IntentCategory.SCREEN_ANALYSIS,
                action="analyze",
                params={"prompt": "Describe what's visible on the user's screen in detail."},
            )

        # Cursor-context questions like "can you find his linkedin" / "who is this person"
        if re.search(r"(?:find\s+(?:his|her|their)\s+|who\s+is\s+(?:this|that)\s*(?:person|guy|man|woman)?)", text):
            prompt = text
            return Intent(
                category=IntentCategory.CURSOR_ANALYSIS,
                action="analyze",
                params={"prompt": f"The user is pointing at something on screen and asks: {prompt}"},
            )

        # ===================================================================
        # 30. Weather & Temperature
        # ===================================================================

        if re.search(r"\b(weather|temperature|forecast|whether)\b", text):
            loc_match = re.search(r"\b(?:in|for|at)\s+([a-zA-Z\s]+)$", text)
            location = loc_match.group(1).strip() if loc_match else ""
            return Intent(
                category=IntentCategory.WEATHER,
                action="get_weather",
                params={"location": location},
                confirmation_prompt="Checking the live weather for you, sir.",
            )

        return None

