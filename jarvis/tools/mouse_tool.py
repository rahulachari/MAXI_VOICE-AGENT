"""
JARVIS Mouse Automation Tool
Fallback for cursor movement, clicks, and page scrolling.
"""

import pyautogui
from .base import BaseTool, ToolResult


class MouseTool(BaseTool):
    name = "MouseTool"
    description = "Handles mouse clicks, movements, and scroll events."

    def execute(self, action: str, **kwargs) -> ToolResult:
        action = action.lower().strip()

        if action == "click":
            x = kwargs.get("x")
            y = kwargs.get("y")
            button = kwargs.get("button", "left")
            try:
                if x is not None and y is not None:
                    pyautogui.click(x=x, y=y, button=button)
                else:
                    pyautogui.click(button=button)
                return ToolResult(status="SUCCESS", message="Clicked mouse.")
            except Exception as e:
                return ToolResult(status="FAILED", message=f"Click failed: {e}", error=str(e))

        elif action == "scroll":
            amount = kwargs.get("amount", -300)  # Negative is scroll down in pyautogui
            direction = kwargs.get("direction", "down").lower()
            if direction == "up" and amount < 0:
                amount = abs(amount)
            elif direction == "down" and amount > 0:
                amount = -amount

            try:
                pyautogui.scroll(amount)
                return ToolResult(status="SUCCESS", message=f"Scrolled {direction}.")
            except Exception as e:
                return ToolResult(status="FAILED", message=f"Scroll failed: {e}", error=str(e))

        return ToolResult(status="FAILED", message=f"Unknown mouse action: {action}")
