"""
JARVIS Tool Interface Base Architecture
Every tool returns a structured ToolResult with status, output, and parameters.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class ToolResult:
    status: str  # 'SUCCESS', 'FAILED', 'REQUIRES_CONFIRMATION', 'REQUIRES_CLARIFICATION', 'CANCELLED'
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    requires_confirmation: bool = False
    confirmation_prompt: str = ""
    next_steps: list = field(default_factory=list)

    def is_success(self) -> bool:
        return self.status == "SUCCESS"


class BaseTool(ABC):
    name: str = "base_tool"
    description: str = ""

    @abstractmethod
    def execute(self, action: str, **kwargs) -> ToolResult:
        pass
