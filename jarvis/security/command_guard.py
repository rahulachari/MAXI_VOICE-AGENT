"""
JARVIS Security & Command Guard
Evaluates actions, shell commands, and file operations for safety.
"""

import re
from typing import Tuple

DANGEROUS_PATTERNS = [
    r"\bformat\b",
    r"\brmdir\s+/[sS]\b",
    r"\bdel\s+/[fFqQsS]\b",
    r"\bRemove-Item\b.*-[rR]ecurse",
    r"\bshutdown\s+/[rRsS]\b",
    r"\breg\s+delete\b",
    r"\bDrop\s+Table\b",
    r"\bDiskpart\b",
]

CONSEQUENTIAL_ACTIONS = [
    "delete_file",
    "delete_folder",
    "send_email",
    "send_message",
    "purchase",
    "execute_shell",
]


class CommandGuard:
    @staticmethod
    def assess_shell_risk(cmd: str) -> Tuple[str, str]:
        """
        Assesses risk of a shell command.
        Returns: (risk_level, explanation)
        risk_level is 'SAFE', 'MODERATE', or 'DANGEROUS'.
        """
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, cmd, re.IGNORECASE):
                return "DANGEROUS", f"Command matches high-risk pattern: {pattern}"

        if any(token in cmd.lower() for token in ["delete", "remove", "kill", "taskkill", "stop-process"]):
            return "MODERATE", "Command may terminate processes or alter system files."

        return "SAFE", "Command considered safe for automated execution."

    @staticmethod
    def requires_confirmation(action_type: str) -> bool:
        """Determines if an action category requires voice/click confirmation."""
        return action_type in CONSEQUENTIAL_ACTIONS
