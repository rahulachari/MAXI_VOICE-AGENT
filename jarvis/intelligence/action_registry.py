"""
JARVIS Action Registry & Validation Layer
Defines explicit tool schemas, required parameter checks, and single-turn clarifying questions.
"""

from typing import Dict, Any, List, Optional, Tuple
from .intent import Intent, IntentCategory


ACTION_REGISTRY: Dict[str, Dict[str, Any]] = {
    "compose_email": {
        "category": IntentCategory.EMAIL,
        "description": "Draft or compose an email",
        "required_params": ["recipient"],
        "clarifying_questions": {
            "recipient": "Who should I address the email to?",
        },
    },
    "send_whatsapp": {
        "category": IntentCategory.MESSAGING,
        "description": "Send a WhatsApp message to a contact",
        "required_params": ["contact"],
        "clarifying_questions": {
            "contact": "Which contact would you like to message on WhatsApp?",
        },
    },
    "send_telegram": {
        "category": IntentCategory.MESSAGING,
        "description": "Send a Telegram message to a contact",
        "required_params": ["contact"],
        "clarifying_questions": {
            "contact": "Which contact would you like to message on Telegram?",
        },
    },
    "create_event": {
        "category": IntentCategory.CALENDAR,
        "description": "Create a calendar event or scheduled reminder",
        "required_params": ["title"],
        "clarifying_questions": {
            "title": "What should the title of the event or reminder be?",
        },
    },
    "add_task": {
        "category": IntentCategory.TASK,
        "description": "Add an item to the task or to-do list",
        "required_params": ["title"],
        "clarifying_questions": {
            "title": "What task or reminder should I hold for you?",
        },
    },
    "play_youtube": {
        "category": IntentCategory.MUSIC,
        "description": "Play a song or video on YouTube",
        "required_params": ["query"],
        "clarifying_questions": {
            "query": "What song or video would you like me to play?",
        },
    },
    "play_spotify": {
        "category": IntentCategory.MUSIC,
        "description": "Play music or a playlist on Spotify",
        "required_params": ["query"],
        "clarifying_questions": {
            "query": "What artist, song, or playlist should I play on Spotify?",
        },
    },
    "open_folder": {
        "category": IntentCategory.FILE_OPEN,
        "description": "Open a directory in File Explorer",
        "required_params": ["folder"],
        "clarifying_questions": {
            "folder": "Which folder would you like to explore?",
        },
    },
    "open_file": {
        "category": IntentCategory.FILE_OPEN,
        "description": "Open a specific file",
        "required_params": ["query"],
        "clarifying_questions": {
            "query": "Which file should I find and open for you?",
        },
    },
    "launch_app": {
        "category": IntentCategory.APP_LAUNCH,
        "description": "Launch an installed Windows application",
        "required_params": ["app_name"],
        "clarifying_questions": {
            "app_name": "Which app would you like me to launch?",
        },
    },
}


def validate_intent_parameters(intent: Intent) -> Optional[Tuple[str, str]]:
    """
    Checks if an intent has all required parameters.
    If a required parameter is missing, returns (missing_param_key, clarifying_question).
    If valid, returns None.
    """
    if not intent or not intent.action:
        return None

    schema = ACTION_REGISTRY.get(intent.action)
    if not schema:
        return None

    required = schema.get("required_params", [])
    questions = schema.get("clarifying_questions", {})

    for param in required:
        val = intent.params.get(param)
        if not val or not str(val).strip():
            question = questions.get(param, f"Could you specify the {param} for this action?")
            return (param, question)

    return None
