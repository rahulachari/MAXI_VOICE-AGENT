"""
JARVIS Text Formatting & Sanitization Engine
Ensures generated emails, messages, tasks, and speech never contain
raw markdown artifacts (#, ##, **, bullets), filler words (um, uh),
or stuttered repetitions, while preserving markdown for markdown-native targets (Notion/Obsidian).
"""

import re
from typing import Optional

FILLER_WORDS = [
    r"\bum+\b",
    r"\buh+\b",
    r"\ber+\b",
    r"\bah+\b",
    r"\byou\s+know\b",
]

# Patterns for repeated words (e.g. "I I", "the the", "we we")
REPEATED_WORDS_PATTERN = re.compile(r"\b(\w+)\s+\1\b", re.IGNORECASE)


def strip_filler_words(text: str) -> str:
    """Removes verbal filler words (um, uh, er, ah, you know) and stutters."""
    if not text:
        return ""
    
    t = text
    # 1. Self-correction handling: e.g. "actually I mean tomorrow" -> "tomorrow"
    if "actually i mean" in t.lower():
        parts = re.split(r"actually\s+i\s+mean", t, flags=re.IGNORECASE)
        t = parts[-1].strip()
    elif "no i mean" in t.lower():
        parts = re.split(r"no\s+i\s+mean", t, flags=re.IGNORECASE)
        t = parts[-1].strip()

    # 2. Filler word patterns
    for pat in FILLER_WORDS:
        t = re.sub(pat, "", t, flags=re.IGNORECASE)

    # 3. Remove repeated stuttered words ("the the" -> "the", "I I" -> "I")
    # Loop twice in case of triple repetitions
    t = REPEATED_WORDS_PATTERN.sub(r"\1", t)
    t = REPEATED_WORDS_PATTERN.sub(r"\1", t)

    # 4. Clean extra spaces
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\s+([,.?!])", r"\1", t)
    return t.strip()


def strip_markdown(text: str) -> str:
    """
    Transforms markdown into clean human-readable plain text without syntax tokens:
    - # Heading -> Heading (surrounded by linebreaks)
    - **bold** / *italic* -> bold / italic
    - [Link](url) -> Link (url) or just Link
    - ```code``` -> code
    - Bullet lines (- or *) -> clean text or indented lines without asterisks
    """
    if not text:
        return ""

    t = text

    # Remove JSON wrapper if accidentally returned as raw JSON
    if t.strip().startswith("{") and t.strip().endswith("}"):
        try:
            import json
            data = json.loads(t)
            t = data.get("spoken_response") or data.get("message") or data.get("answer") or data.get("full_details") or t
        except Exception:
            pass

    # 1. Code blocks: strip triple backticks, keep code content
    t = re.sub(r"```[\w]*\n?(.*?)```", r"\1", t, flags=re.DOTALL)
    # Inline code ticks: `code` -> code
    t = re.sub(r"`([^`]+)`", r"\1", t)

    # 2. Markdown headers: '# Header' -> '\nHeader\n'
    t = re.sub(r"^#{1,6}\s*(.+)$", r"\n\1\n", t, flags=re.MULTILINE)

    # 3. Bold & Italic: ***text***, **text**, *text*, ___text___, __text__, _text_
    t = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", t)
    t = re.sub(r"_{1,3}([^_]+)_{1,3}", r"\1", t)

    # 4. Markdown links: [Text](URL) -> Text
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", t)

    # 5. Bullet points: * Item or - Item -> Item
    t = re.sub(r"^[ \t]*[\*\-\+•]\s+", "", t, flags=re.MULTILINE)

    # 6. Numbered lists: 1. Item -> 1. Item (keep number, remove markdown bold if inside)
    t = re.sub(r"^[ \t]*\d+\.\s+", "", t, flags=re.MULTILINE)

    # 7. Blockquotes: > Quote -> Quote
    t = re.sub(r"^[ \t]*>\s*", "", t, flags=re.MULTILINE)

    # 8. Horizontal rules: --- or *** -> blank
    t = re.sub(r"^[\*\-_]{3,}\s*$", "", t, flags=re.MULTILINE)

    # 9. Clean up stray asterisks, hashes, tildes, backticks
    t = re.sub(r"[#\*~`]", "", t)

    # 10. Normalize multiple blank lines to at most two
    t = re.sub(r"\n{3,}", "\n\n", t)
    t = re.sub(r"[ \t]+", " ", t)

    return t.strip()


def clean_for_plain_text(text: str, target: str = "plain") -> str:
    """
    Cleans and formats text based on the destination target.
    If target is 'notion' or 'obsidian', markdown formatting is preserved.
    Otherwise (email, message, whatsapp, slack, word, plain), markdown is stripped
    and converted to natural human-written prose.
    """
    if not text:
        return ""

    # Check if target supports native markdown
    t_lower = (target or "").lower()
    if any(m in t_lower for m in ["notion", "obsidian", "markdown", "md"]):
        # Keep markdown, but strip filler words
        return strip_filler_words(text)

    # Plain text target: strip markdown and filler words
    cleaned = strip_markdown(text)
    cleaned = strip_filler_words(cleaned)

    # Capitalize first letter of sentences
    sentences = re.split(r"([.?!]\s+)", cleaned)
    capitalized = []
    for s in sentences:
        if s and not re.match(r"^[.?!]\s+$", s):
            s = s[0].upper() + s[1:] if len(s) > 1 else s.upper()
        capitalized.append(s)

    return "".join(capitalized).strip()


def clean_spoken_text(text: str) -> str:
    """
    Cleans text for speech synthesis and voice HUD readout:
    Strips markdown, emojis, URLs, symbols, fillers, and ensures articulate natural cadence.
    """
    if not text:
        return ""

    t = strip_markdown(text)
    t = strip_filler_words(t)

    # Remove emojis
    t = re.sub(r"[\U0001F300-\U0001F9FF\U00002600-\U000027BF\U0001FA00-\U0001FA6F]", "", t)

    # Remove URLs
    t = re.sub(r"https?://\S+", "", t)

    # Remove stray punctuation/special chars
    t = re.sub(r"[\{\}\[\]\"\\|<>~_]", "", t)

    # Normalize whitespace
    t = re.sub(r"\n+", ". ", t)
    t = re.sub(r"\s+", " ", t).strip()

    return t


def clean_dictated_text(raw_text: str, target_app: str = "") -> str:
    """
    Prepares speech-to-text dictation for insertion into active window or clipboard:
    Removes fillers, fixes punctuation spacing, and capitalizes.
    """
    return clean_for_plain_text(raw_text, target=target_app)
